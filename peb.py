import argparse
import sys
import os
import configparser
from pathlib import Path
from database import Database
from datetime import datetime
from tabulate import tabulate
import json
import shutil
import zipfile

class ProjEB:
    def __init__(self, api_mode=False):
        self.api_mode = api_mode
        self.config = self._load_config()
        try:
            self.db = Database(self.config['database']['file'])
            # Verify database connection works
            if not self.db.connect():
                raise RuntimeError("Database connection failed")
            self._ensure_directories()
        except (sqlite3.Error, OSError, RuntimeError) as e:
            raise RuntimeError(f"Database initialization failed: {str(e)}")

    def _load_config(self):
        """Load configuration from ini file"""
        config = configparser.ConfigParser()
        config_file = os.environ.get('PROJEB_CONFIG', 'configuration.ini')
        
        if not config.read(config_file):
            raise RuntimeError(f"Could not read configuration file: {config_file}")
            
        # Validate required sections and options
        required_sections = ['database', 'attachments', 'backup', 'export']
        for section in required_sections:
            if section not in config:
                raise RuntimeError(f"Missing required section '{section}' in config file")
                
        if 'file' not in config['database']:
            raise RuntimeError("Missing required 'file' option in [database] section")
            
        return config

    def _ensure_directories(self):
        """Ensure required directories exist"""
        dirs = [
            self.config['attachments']['dir'],
            self.config['backup']['dir'],
            self.config['export']['dir']
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def _output(self, message, data=None):
        """Handle output based on mode"""
        if self.api_mode:
            return {"message": message, "data": data}
        else:
            if data:
                if isinstance(data, list):
                    print(tabulate(data, headers='keys', tablefmt='grid'))
                else:
                    print(data)
            print(message)

    def create_notebook(self, args):
        """Create a new notebook"""
        notebook_id = self.db.create_notebook(args.name, args.description)
        data = {'id': notebook_id} if notebook_id else None
        return self._output(
            "Notebook created successfully" if notebook_id else "Failed to create notebook",
            data
        )

    def list_notebooks(self, args):
        """List all notebooks"""
        notebooks = self.db.get_notebooks()
        formatted_notebooks = []
        for nb in notebooks:
            formatted_notebooks.append({
                'ID': nb[0],
                'Name': nb[1],
                'Description': nb[2],
                'Created': nb[3],
                'Status': nb[4]
            })
        return self._output("Notebooks:", formatted_notebooks)

    def create_entry(self, args):
        """Create a new entry in a notebook"""
        notebook_id = None
        
        # Handle both notebook name and notebook_id
        if hasattr(args, 'notebook') and args.notebook:
            notebook = self.db.get_notebook_by_name(args.notebook)
            if notebook:
                notebook_id = notebook[0]  # Get ID from notebook tuple
        elif hasattr(args, 'notebook_id') and args.notebook_id:
            # Verify notebook_id exists
            notebooks = self.db.get_notebooks()
            if not any(nb[0] == args.notebook_id for nb in notebooks):
                return self._output(f"Failed to create entry: Notebook ID {args.notebook_id} not found", None)
            notebook_id = args.notebook_id
        
        if not notebook_id:
            return self._output(f"Failed to create entry: Notebook not found", None)
        
        attachments = args.attachments.split(',') if args.attachments else None
        
        # Verify attachments exist if specified
        if attachments:
            for attachment in attachments:
                if not Path(attachment).exists():
                    return self._output(
                        f"Failed to create entry: Attachment not found: {attachment}",
                        None
                    )
        
        # Create entry
        entry_id = self.db.create_entry(
            notebook_id,
            args.title,
            args.content,
            attachments
        )
        
        if entry_id and args.tags:
            for tag_name in args.tags.split(','):
                tag_id = self.db.create_tag(tag_name)
                if tag_id:
                    self.db.add_tag_to_entry(entry_id, tag_id)
        
        data = {'id': entry_id} if entry_id else None
        return self._output(
            "Entry created successfully" if entry_id else "Failed to create entry",
            data
        )

    def merge_tags(self, args):
        """Merge multiple tags into one"""
        try:
            tag_ids = [int(tid.strip()) for tid in args.tags.split(',')]
            result = self.db.merge_tags(tag_ids, args.new_tag)
            return self._output(
                "Tags merged successfully" if result else "Failed to merge tags"
            )
        except ValueError as e:
            return self._output(f"Failed to merge tags: Invalid tag IDs - {str(e)}")

    def create_note(self, args):
        """Create a new note for an entry"""
        attachments = args.attachments.split(',') if args.attachments else None
        note_id = self.db.create_note(args.entry_id, args.content, attachments)
        
        if note_id and args.tags:
            for tag_name in args.tags.split(','):
                tag_id = self.db.create_tag(tag_name)
                self.db.add_tag_to_note(note_id, tag_id)
        
        data = {'id': note_id} if note_id else None
        return self._output(
            "Note created successfully" if note_id else "Failed to create note",
            data
        )

    def list_notes(self, args):
        """List notes for an entry"""
        notes = self.db.get_notes(args.entry_id)
        formatted_notes = []
        for note in notes:
            formatted_notes.append({
                'ID': note[0],
                'Content': note[1],
                'Created': note[2]
            })
        return self._output("Notes:", formatted_notes)

    def search(self, args):
        """Search entries and notes"""
        results = self.db.search(args.query, args.tag)
        formatted_results = []
        for result in results:
            formatted_results.append({
                'ID': result[0],
                'NotebookID': result[1],
                'Title': result[2],
                'Content': result[3],
                'Created': result[4]
            })
        return self._output("Search results:", formatted_results)

    def export_data(self, args):
        """Export data to JSON format"""
        try:
            export_dir = Path(self.config['export']['dir'])
            
            # Test if directory is writable by attempting to create a test file
            test_file = export_dir / '.write_test'
            try:
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError):
                return self._output(f"Export failed: Directory {export_dir} is not writable")
            
            export_data = {
                'notebooks': self.db.get_notebooks(),
                'entries': self.db.get_entries(),
                'notes': [],
                'tags': self.db.get_tags()
            }
            
            export_path = export_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
                
            return self._output(f"Data exported to {export_path}")
        except (PermissionError, OSError) as e:
            return self._output(f"Export failed: {str(e)}")

    def import_data(self, args):
        """Import data from JSON file"""
        try:
            with open(args.file, 'r') as f:
                import_data = json.load(f)
                
            # Import notebooks and store ID mappings
            notebook_map = {}
            for notebook in import_data.get('notebooks', []):
                new_id = self.db.create_notebook(notebook[1], notebook[2])
                notebook_map[notebook[0]] = new_id
                
            # Import entries with updated notebook IDs
            entry_map = {}
            for entry in import_data.get('entries', []):
                new_notebook_id = notebook_map.get(entry[1])
                if new_notebook_id:
                    new_id = self.db.create_entry(
                        new_notebook_id,
                        entry[2],
                        entry[3]
                    )
                    entry_map[entry[0]] = new_id
                    
            # Import tags
            tag_map = {}
            for tag in import_data.get('tags', []):
                new_id = self.db.create_tag(tag[1], tag[2])
                tag_map[tag[0]] = new_id
                
            # Import entry-tag relationships
            for entry in import_data.get('entries', []):
                old_entry_id = entry[0]
                new_entry_id = entry_map.get(old_entry_id)
                if new_entry_id:
                    # Get tags for this entry from original database
                    entry_tags = self.db.get_entry_tags(old_entry_id)
                    for tag in entry_tags:
                        new_tag_id = tag_map.get(tag[0])
                        if new_tag_id:
                            self.db.add_tag_to_entry(new_entry_id, new_tag_id)
                
            return self._output("Data imported successfully")
        except Exception as e:
            return self._output(f"Import failed: {str(e)}")

    def backup(self, args):
        """Create a backup of the entire ELN"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Get absolute path of backup directory
            backup_dir = Path(self.config['backup']['dir']).resolve()
            
            # If backup directory is relative, make it relative to config file location
            if not backup_dir.is_absolute():
                config_dir = Path(os.environ.get('PROJEB_CONFIG', 'configuration.ini')).parent
                backup_dir = (config_dir / self.config['backup']['dir']).resolve()
                
            # Create backup directory if it doesn't exist
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_path = backup_dir / f"backup_{timestamp}.zip"
            
            # Test if directory is writable
            test_file = backup_dir / '.write_test'
            try:
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError):
                return self._output(f"Backup failed: Directory {backup_dir} is not writable")
                
            with zipfile.ZipFile(backup_path, 'w') as backup_zip:
                # Backup database using absolute paths
                db_path = Path(self.config['database']['file']).resolve()
                if not db_path.exists():
                    return self._output(f"Backup failed: Database file not found at {db_path}")
                backup_zip.write(db_path, db_path.name)
                
                # Backup attachments using absolute paths
                attachments_dir = Path(self.config['attachments']['dir']).resolve()
                if attachments_dir.exists():
                    for file_path in attachments_dir.rglob('*'):
                        if file_path.is_file():
                            rel_path = file_path.relative_to(attachments_dir)
                            backup_zip.write(file_path, f"attachments/{rel_path}")
            
            return self._output(f"Backup created at {backup_path}")
        except (PermissionError, OSError) as e:
            return self._output(f"Backup failed: {str(e)}")

    def restore(self, args):
        """Restore ELN from backup"""
        try:
            backup_path = Path(args.backup_file)
            if not backup_path.exists():
                return self._output(f"Backup file not found: {backup_path}")
                
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                # Close current database connection
                self.db.close()
                
                # Get database path
                db_path = Path(self.config['database']['file'])
                db_name = db_path.name
                
                # Extract database
                backup_zip.extract(db_name, db_path.parent)
                
                # Extract attachments
                attachments_dir = Path(self.config['attachments']['dir'])
                for file_info in backup_zip.filelist:
                    if file_info.filename.startswith('attachments/'):
                        backup_zip.extract(file_info.filename, attachments_dir.parent)
                
                # Reconnect to database
                self.db = Database(str(db_path))
                
            return self._output("Restore completed successfully")
        except Exception as e:
            return self._output(f"Restore failed: {str(e)}")

    def list_tags(self, args):
        """List all tags"""
        tags = self.db.get_tags()
        formatted_tags = []
        for tag in tags:
            formatted_tags.append({
                'ID': tag[0],
                'Name': tag[1],
                'Description': tag[2]
            })
        return self._output("Tags:", formatted_tags)

    def create_tag(self, name, description=""):
        """Create a new tag or get existing one."""
        # First try to get existing tag
        sql_get = """SELECT id FROM tags WHERE name = ?"""
        
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql_get, (name,))
            existing = cur.fetchone()
            if existing:
                return existing[0]
                
            # Tag doesn't exist, create it
            sql_create = """INSERT INTO tags(name, description)
                           VALUES(?, ?)"""
            cur.execute(sql_create, (name, description))
            conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating tag: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='ProjEB - Project Electronic Book')
    parser.add_argument('--api', action='store_true', help='Run in API mode')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Notebook commands
    notebook_create = subparsers.add_parser('create-notebook', help='Create a new notebook')
    notebook_create.add_argument('--name', required=True, help='Notebook name')
    notebook_create.add_argument('--description', help='Notebook description')

    subparsers.add_parser('list-notebooks', help='List all notebooks')

    # Entry commands
    entry_create = subparsers.add_parser('create-entry', help='Create a new entry')
    entry_create.add_argument('--notebook', help='Notebook name')  # Changed from notebook-id
    entry_create.add_argument('--notebook-id', type=int, help='Notebook ID')
    entry_create.add_argument('--title', required=True, help='Entry title')
    entry_create.add_argument('--content', help='Entry content')
    entry_create.add_argument('--attachments', help='Comma-separated list of attachment paths')
    entry_create.add_argument('--tags', help='Comma-separated list of tags')

    # Tag commands
    subparsers.add_parser('list-tags', help='List all tags')
    tag_merge = subparsers.add_parser('merge-tags', help='Merge multiple tags')
    tag_merge.add_argument('--tags', required=True, help='Comma-separated list of tag IDs to merge')
    tag_merge.add_argument('--new-tag', required=True, help='Name for the merged tag')

    # Note management
    note_create = subparsers.add_parser('create-note', help='Create a new note')
    note_create.add_argument('--entry-id', required=True, type=int, help='Entry ID')
    note_create.add_argument('--content', required=True, help='Note content')
    note_create.add_argument('--attachments', help='Comma-separated list of attachment paths')
    note_create.add_argument('--tags', help='Comma-separated list of tags')

    note_list = subparsers.add_parser('list-notes', help='List notes for an entry')
    note_list.add_argument('--entry-id', required=True, type=int, help='Entry ID')

    # Search
    search_parser = subparsers.add_parser('search', help='Search entries and notes')
    search_parser.add_argument('--query', required=True, help='Search query')
    search_parser.add_argument('--tag', help='Filter by tag')

    # Export/Import
    export_parser = subparsers.add_parser('export', help='Export data')
    import_parser = subparsers.add_parser('import', help='Import data')
    import_parser.add_argument('--file', required=True, help='Import file path')

    # Backup/Restore
    backup_parser = subparsers.add_parser('backup', help='Create backup')
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('--backup-file', required=True, help='Backup file path')

    # Parse arguments
    args = parser.parse_args()

    # Initialize ProjEB
    peb = ProjEB(api_mode=args.api)

    # Execute command
    if args.command == 'create-notebook':
        result = peb.create_notebook(args)
    elif args.command == 'list-notebooks':
        result = peb.list_notebooks(args)
    elif args.command == 'create-entry':
        result = peb.create_entry(args)
    elif args.command == 'list-tags':
        result = peb.list_tags(args)
    elif args.command == 'merge-tags':
        result = peb.merge_tags(args)
    elif args.command == 'create-note':
        result = peb.create_note(args)
    elif args.command == 'list-notes':
        result = peb.list_notes(args)
    elif args.command == 'search':
        result = peb.search(args)
    elif args.command == 'export':
        result = peb.export_data(args)
    elif args.command == 'import':
        result = peb.import_data(args)
    elif args.command == 'backup':
        result = peb.backup(args)
    elif args.command == 'restore':
        result = peb.restore(args)
    else:
        parser.print_help()
        sys.exit(1)

    # Return result if in API mode
    if args.api:
        sys.exit(0 if result.get('data') is not None else 1)

if __name__ == '__main__':
    main()
