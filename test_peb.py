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
        self.db = Database(self.config['database']['file'])
        self._ensure_directories()
        self.tag = None

    def _load_config(self):
        """Load configuration from ini file"""
        config = configparser.ConfigParser()
        config_file = os.environ.get('PROJEB_CONFIG', 'configuration.ini')
        config.read(config_file)
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
        attachments = args.attachments.split(',') if args.attachments else None
        entry_id = self.db.create_entry(
            args.notebook_id,
            args.title,
            args.content,
            attachments
        )
        if entry_id and args.tags:
            for tag_name in args.tags.split(','):
                tag_id = self.db.create_tag(tag_name)
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
                'Title': result[1],
                'Content': result[2],
                'Created': result[3]
            })
        return self._output("Search results:", formatted_results)

    def export_data(self, args):
        """Export data to JSON format"""
        export_data = {
            'notebooks': self.db.get_notebooks(),
            'entries': self.db.get_entries(),
            'notes': [],
            'tags': self.db.get_tags()
        }
        
        export_path = Path(self.config['export']['dir']) / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
            
        return self._output(f"Data exported to {export_path}")

    def import_data(self, args):
        """Import data from JSON file"""
        try:
            with open(args.file, 'r') as f:
                import_data = json.load(f)
            
            for notebook in import_data.get('notebooks', []):
                self.db.create_notebook(notebook[1], notebook[2])
            # Import other data...
            
            return self._output("Data imported successfully")
        except Exception as e:
            return self._output(f"Import failed: {str(e)}")

    def backup(self, args):
        """Create a backup of the entire ELN"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path(self.config['backup']['dir'])
        backup_path = backup_dir / f"backup_{timestamp}.zip"
        
        with zipfile.ZipFile(backup_path, 'w') as backup_zip:
            # Backup database
            backup_zip.write(self.config['database']['file'])
            
            # Backup attachments
            attachments_dir = Path(self.config['attachments']['dir'])
            for file_path in attachments_dir.rglob('*'):
                if file_path.is_file():
                    backup_zip.write(file_path, file_path.relative_to(attachments_dir))
        
        return self._output(f"Backup created at {backup_path}")

    def restore(self, args):
        """Restore ELN from backup"""
        try:
            with zipfile.ZipFile(args.backup_file, 'r') as backup_zip:
                # Close current database connection
                self.db.close()
                
                # Restore database
                backup_zip.extract(Path(self.config['database']['file']).name)
                
                # Restore attachments
                attachments_dir = Path(self.config['attachments']['dir'])
                for file_info in backup_zip.filelist:
                    if not file_info.filename.endswith('.db'):
                        backup_zip.extract(file_info, attachments_dir)
                
                # Reconnect to database
                self.db = Database(self.config['database']['file'])
                
            return self._output("Restore completed successfully")
        except Exception as e:
            return self._output(f"Restore failed: {str(e)}")

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
    entry_create.add_argument('--notebook-id', required=True, type=int, help='Notebook ID')
    entry_create.add_argument('--title', required=True, help='Entry title')
    entry_create.add_argument('--content', help='Entry content')
    entry_create.add_argument('--attachments', help='Comma-separated list of attachment paths')
    entry_create.add_argument('--tags', help='Comma-separated list of tags')

    # Tag commands
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

import unittest
import os
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from database import Database
from peb import ProjEB

class Args:
    """Mock class for command line arguments"""
    def __init__(self, **kwargs):
        # Set default values
        self.attachments = None
        self.tags = None
        self.content = None
        self.description = None
        self.tag = None
        self.query = None
        self.name = None
        self.notebook = None  # Add this line
        self.notebook_id = None  # Keep for backward compatibility
        self.entry_id = None
        self.title = None
        self.new_tag = None
        # Override with provided values
        for key, value in kwargs.items():
            setattr(self, key, value)

class TestProjEB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment"""
        cls.original_config = os.environ.get('PROJEB_CONFIG', None)
        cls.base_dir = Path.cwd() / 'test_data'
        if cls.base_dir.exists():
            shutil.rmtree(cls.base_dir)
        cls.base_dir.mkdir()

    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create test directories with absolute paths
        self.test_dir = self.base_dir  # Add this line to fix missing attribute
        self.db_file = self.base_dir / "test.db"
        
        # Clear existing database
        if self.db_file.exists():
            try:
                if hasattr(self, 'peb'):
                    self.peb.db.close()
                os.remove(self.db_file)
            except (PermissionError, OSError):
                pass
        
        self.dirs = {
            'attachments': self.base_dir / 'attachments',
            'backups': self.base_dir / 'backups',
            'exports': self.base_dir / 'exports'
        }
        
        # Create directories
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create test configuration
        self.config_path = self.base_dir / 'test_config.ini'
        config_content = f"""
[database]
file = {str(self.db_file.absolute())}

[attachments]
dir = {str(self.dirs['attachments'].absolute())}

[backup]
dir = {str(self.dirs['backups'].absolute())}

[export]
dir = {str(self.dirs['exports'].absolute())}
"""
        self.config_path.write_text(config_content)
        
        # Set test configuration
        os.environ['PROJEB_CONFIG'] = str(self.config_path.absolute())
        
        # Create fresh ProjEB instance
        self.peb = ProjEB(api_mode=True)

    def tearDown(self):
        """Clean up after each test"""
        try:
            # Close database connection
            if hasattr(self, 'peb'):
                self.peb.db.close()
                self.peb = None
            
            # Remove test database
            if self.db_file.exists():
                os.remove(self.db_file)
            
        finally:
            # Restore original config environment variable
            if self.original_config:
                os.environ['PROJEB_CONFIG'] = self.original_config
            else:
                os.environ.pop('PROJEB_CONFIG', None)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Remove test directory and all contents
            if cls.base_dir.exists():
                shutil.rmtree(cls.base_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Failed to clean up test directory: {e}")

    def test_notebook_management(self):
        """Test notebook creation and listing"""
        # Ensure clean database
        if hasattr(self, 'peb'):
            self.peb.db.close()
        if self.db_file.exists():
            os.remove(self.db_file)
        self.peb = ProjEB(api_mode=True)
        
        # Create notebook
        notebook_name = f"Test_Notebook_{os.urandom(4).hex()}"
        result = self.peb.create_notebook(Args(
            name=notebook_name,
            description='Test Description'
        ))
        
        self.assertEqual(result['message'], "Notebook created successfully")
        self.assertIsNotNone(result.get('data'))
        self.assertIn('id', result['data'])
        
        # List notebooks
        list_result = self.peb.list_notebooks(None)
        self.assertEqual(len(list_result['data']), 1, 
                        "Expected exactly one notebook in database")
        self.assertEqual(list_result['data'][0]['Name'], notebook_name)

    def test_entry_management(self):
        """Test entry creation and management"""
        # Create notebook first
        notebook_name = f"Test_Notebook_{os.urandom(4).hex()}"
        notebook = self.peb.create_notebook(Args(
            name=notebook_name,
            description='Test Description'
        ))
        
        # Create entry
        entry_result = self.peb.create_entry(Args(
            notebook=notebook_name,  # Changed from notebook_id
            title='Test Entry',
            content='Test Content'
        ))
        
        self.assertEqual(entry_result['message'], "Entry created successfully")
        self.assertIsNotNone(entry_result.get('data'))
        self.assertIn('id', entry_result['data'])

    def test_note_management(self):
        """Test note creation and management"""
        # Create notebook and entry first
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        
        entry = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Test Entry',
            content='Test Content'
        ))
        
        # Create note
        note_result = self.peb.create_note(Args(
            entry_id=entry['data']['id'],
            content='Test Note Content'
        ))
        
        self.assertEqual(note_result['message'], "Note created successfully")
        self.assertIsNotNone(note_result.get('data'))
        self.assertIn('id', note_result['data'])

    def test_search_functionality(self):
        """Test search capabilities"""
        # Create notebook and entry with searchable content
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        
        # Create entry with unique searchable content
        unique_term = f"SEARCHTERM_{os.urandom(4).hex()}"
        entry = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Test Entry',
            content=f'Test content with {unique_term} here'
        ))
        
        # Search for the unique term
        search_result = self.peb.search(Args(
            query=unique_term,
            tag=None
        ))
        
        # Verify search results
        self.assertGreater(len(search_result['data']), 0, 
                      "No search results found")
    
        found = False
        for item in search_result['data']:
            if unique_term in str(item.get('Content', '')):
                found = True
                break
            
        self.assertTrue(found, 
                   f"Search term '{unique_term}' not found in results")
    
        # Verify the complete entry data
        matching_entry = next(
            (item for item in search_result['data'] 
             if unique_term in str(item.get('Content', ''))),
            None
        )
        self.assertIsNotNone(matching_entry, 
                        "Could not find matching entry in results")
        self.assertEqual(matching_entry['NotebookID'], 
                    notebook['data']['id'])

    def test_tag_management(self):
        """Test tag operations"""
        # Create notebook and entry with tags
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        self.assertIsNotNone(notebook.get('data'))
        notebook_id = notebook['data']['id']
        
        # Create unique tag names
        tag1_name = f"tag1_{os.urandom(4).hex()}"
        tag2_name = f"tag2_{os.urandom(4).hex()}"
        
        # Create entry with tags
        entry = self.peb.create_entry(Args(
            notebook_id=notebook_id,
            title='Test Entry',
            content='Test Content',
            attachments=None,
            tags=f"{tag1_name},{tag2_name}"
        ))
        self.assertIsNotNone(entry.get('data'))
        
        # Get tag IDs
        tag1 = self.peb.db.get_tag_by_name(tag1_name)
        tag2 = self.peb.db.get_tag_by_name(tag2_name)
        self.assertIsNotNone(tag1, "First tag not created")
        self.assertIsNotNone(tag2, "Second tag not created")
        
        # Create new tag name for merge
        merged_tag_name = f"merged_tag_{os.urandom(4).hex()}"
        
        # Merge tags
        result = self.peb.merge_tags(Args(
            tags=f"{tag1[0]},{tag2[0]}",
            new_tag=merged_tag_name
        ))
        
        # Verify merge result
        self.assertEqual(result['message'], "Tags merged successfully")
        
        # Verify merged tag exists
        merged_tag = self.peb.db.get_tag_by_name(merged_tag_name)
        self.assertIsNotNone(merged_tag, "Merged tag not found")
        
        # Verify old tags don't exist
        self.assertIsNone(self.peb.db.get_tag_by_name(tag1_name), 
                          "First tag still exists after merge")
        self.assertIsNone(self.peb.db.get_tag_by_name(tag2_name), 
                          "Second tag still exists after merge")

    def test_backup_restore_functionality(self):
        """Test backup and restore functionality"""
        # Create initial test data
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        self.assertIsNotNone(notebook.get('data'))
        
        entry = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Test Entry',
            content='Test Content',
            tags='tag1,tag2'
        ))
        self.assertIsNotNone(entry.get('data'))
        
        # Create backup
        backup_result = self.peb.backup(Args())
        self.assertTrue(backup_result['message'].startswith('Backup created at'))
        
        # Get backup file path from backups directory
        backup_file = None
        for line in backup_result['message'].splitlines():
            if 'Backup created at' in line:
                backup_path = line.split('at')[-1].strip()
                backup_file = self.dirs['backups'] / Path(backup_path).name
                break
        
        self.assertIsNotNone(backup_file, "Backup file path not found in output")
        self.assertTrue(backup_file.exists(), f"Backup file not found at {backup_file}")
        
        # Store original data for comparison
        original_notebooks = self.peb.list_notebooks(None)
        original_tags = self.peb.list_tags(None)
        
        # Close database connection before file operations
        self.peb.db.close()
        
        # Clean database
        if self.db_file.exists():
            os.remove(self.db_file)
        self.assertFalse(self.db_file.exists())
        
        # Create fresh ProjEB instance for restore
        self.peb = ProjEB(api_mode=True)
        
        # Restore from backup
        restore_result = self.peb.restore(Args(backup_file=str(backup_file)))
        self.assertEqual(restore_result['message'], 'Restore completed successfully')
        
        # Verify restored data
        restored_notebooks = self.peb.list_notebooks(None)
        restored_tags = self.peb.list_tags(None)
        
        self.assertEqual(restored_notebooks['data'], original_notebooks['data'])
        self.assertEqual(restored_tags['data'], original_tags['data'])

    def test_export_import_functionality(self):
        """Test export and import functionality"""
        # Create test data with a static name
        notebook_name = "Test_Export_Import_Notebook"
        notebook = self.peb.create_notebook(Args(
            name=notebook_name,
            description='Test Description'
        ))
        self.assertIsNotNone(notebook.get('data'))
        
        # Clean up timestamps and normalize IDs for comparison
        def clean_data(data):
            for item in data:
                item['Created'] = 'TIMESTAMP'
                if 'Name' in item and '_' in item['Name']:
                    item['Name'] = item['Name'].split('_')[0] + '_ID'
                # Reset IDs to normalized values
                if 'ID' in item:
                    item['ID'] = 1
        
        # Store original data and clean it
        original_notebooks = self.peb.list_notebooks(None)
        clean_data(original_notebooks['data'])
        
        # Export and reimport data
        export_result = self.peb.export_data(Args())
        self.assertTrue(export_result['message'].startswith('Data exported to'))
        
        # Clean database and import
        self.peb.db.close()
        os.remove(self.db_file)
        self.peb = ProjEB(api_mode=True)
        
        # Import and verify
        import_result = self.peb.import_data(Args(
            file=str(export_result['message'].split('to ')[-1].strip())
        ))
        self.assertEqual(import_result['message'], 'Data imported successfully')
        
        # Get imported data and clean it
        imported_notebooks = self.peb.list_notebooks(None)
        clean_data(imported_notebooks['data'])
        
        # Compare cleaned data
        self.assertEqual(imported_notebooks['data'], original_notebooks['data'])

    def test_search_with_tags(self):
        """Test search functionality with tag filtering"""
        # Create test data
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        
        # Create entries with different tags
        tag_name = f"searchtag_{os.urandom(4).hex()}"
        entry1 = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Test Entry 1',
            content='Unique content one',
            tags=tag_name
        ))
        
        entry2 = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Test Entry 2',
            content='Unique content two',
            tags='othertag'
        ))
        
        # Search with tag filter
        tag = self.peb.db.get_tag_by_name(tag_name)
        self.assertIsNotNone(tag)
        
        search_result = self.peb.search(Args(
            query='Unique',
            tag=tag[0]
        ))
        
        # Verify only tagged entry is found
        self.assertEqual(len(search_result['data']), 1)
        self.assertIn('one', search_result['data'][0]['Content'])

    def test_config_loading(self):
        """Test configuration loading"""
        # Test valid config
        self.assertIsNotNone(self.peb.config)
        self.assertIn('database', self.peb.config)
        self.assertIn('attachments', self.peb.config)
        self.assertIn('backup', self.peb.config)
        self.assertIn('export', self.peb.config)
        
        # Test invalid config
        with self.assertRaises(RuntimeError):
            os.environ['PROJEB_CONFIG'] = 'nonexistent.ini'
            ProjEB(api_mode=True)

    def test_directory_creation(self):
        """Test required directories are created"""
        # Remove directories
        for dir_path in self.dirs.values():
            if dir_path.exists():
                shutil.rmtree(dir_path)
        
        # Create new ProjEB instance
        peb = ProjEB(api_mode=True)
        
        # Verify directories exist
        for dir_path in self.dirs.values():
            self.assertTrue(dir_path.exists(), f"Directory not created: {dir_path}")

    def test_output_handling(self):
        """Test output handling in different modes"""
        # Test API mode
        peb_api = ProjEB(api_mode=True)
        result = peb_api._output("Test message", {"key": "value"})
        self.assertIsInstance(result, dict)
        self.assertEqual(result["message"], "Test message")
        self.assertEqual(result["data"], {"key": "value"})
        
        # Test CLI mode
        peb_cli = ProjEB(api_mode=False)
        result = peb_cli._output("Test message", {"key": "value"})
        self.assertIsNone(result)

    def test_notebook_validation(self):
        """Test notebook validation"""
        # Test duplicate notebook name
        notebook_name = f"Test_Notebook_{os.urandom(4).hex()}"
        first = self.peb.create_notebook(Args(
            name=notebook_name,
            description='First notebook'
        ))
        self.assertIsNotNone(first.get('data'))
        
        # Try creating notebook with same name
        second = self.peb.create_notebook(Args(
            name=notebook_name,
            description='Second notebook'
        ))
        self.assertIsNone(second.get('data'))

    def test_entry_validation(self):
        """Test entry validation"""
        # Create notebook
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        
        # Test duplicate entry title
        entry_title = f"Test_Entry_{os.urandom(4).hex()}"
        first = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title=entry_title,
            content='First entry'
        ))
        self.assertIsNotNone(first.get('data'))
        
        # Try creating entry with same title
        second = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title=entry_title,
            content='Second entry'
        ))
        self.assertIsNone(second.get('data'))

    def test_attachment_handling(self):
        """Test attachment handling"""
        # Create test file
        test_file = self.dirs['attachments'] / 'test.txt'
        test_file.write_text('Test content')
        
        # Create notebook and entry with attachment
        notebook_name = f"Test_Notebook_{os.urandom(4).hex()}"
        notebook = self.peb.create_notebook(Args(
            name=notebook_name,
            description='Test Description'
        ))
        
        entry = self.peb.create_entry(Args(
            notebook=notebook_name,  # Changed from notebook_id
            title='Test Entry',
            content='Test Content',
            attachments=str(test_file)
        ))
        
        self.assertIsNotNone(entry.get('data'))

    def test_multiple_tag_operations(self):
        """Test complex tag operations"""
        # Create notebook
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        
        # Create tags first to ensure they exist
        tag_names = [f"testtag_{i}_{os.urandom(4).hex()}" for i in range(3)]
        tag_ids = []
        
        for tag_name in tag_names:
            tag_id = self.peb.db.create_tag(tag_name)
            self.assertIsNotNone(tag_id, f"Failed to create tag {tag_name}")
            tag_ids.append(tag_id)
        
        # Create entries with tag combinations
        entry1 = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Entry One',
            content='Content 1'
        ))
        self.assertIsNotNone(entry1.get('data'))
        
        # Add tags to entry1
        self.peb.db.add_tag_to_entry(entry1['data']['id'], tag_ids[0])
        self.peb.db.add_tag_to_entry(entry1['data']['id'], tag_ids[1])
        
        entry2 = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Entry Two',
            content='Content 2'
        ))
        self.assertIsNotNone(entry2.get('data'))
        
        # Add tags to entry2
        self.peb.db.add_tag_to_entry(entry2['data']['id'], tag_ids[1])
        self.peb.db.add_tag_to_entry(entry2['data']['id'], tag_ids[2])
        
        # Verify initial tag assignments
        entry1_initial_tags = self.peb.db.get_entry_tags(entry1['data']['id'])
        entry2_initial_tags = self.peb.db.get_entry_tags(entry2['data']['id'])
        
        self.assertEqual(len(entry1_initial_tags), 2, "Entry 1 should have 2 tags initially")
        self.assertEqual(len(entry2_initial_tags), 2, "Entry 2 should have 2 tags initially")
        
        # Create unique merged tag name
        merged_tag_name = f"merged_tag_{os.urandom(4).hex()}"
        
        # Merge first two tags
        merge_result = self.peb.merge_tags(Args(
            tags=f"{tag_ids[0]},{tag_ids[1]}",
            new_tag=merged_tag_name
        ))
        
        self.assertEqual(merge_result['message'], "Tags merged successfully")
        
        # Verify merged tag exists
        merged_tag = self.peb.db.get_tag_by_name(merged_tag_name)
        self.assertIsNotNone(merged_tag, "Merged tag not found")
        
        # Verify old tags don't exist
        self.assertIsNone(self.peb.db.get_tag_by_name(tag_names[0]), 
                          "First tag still exists after merge")
        self.assertIsNone(self.peb.db.get_tag_by_name(tag_names[1]), 
                          "Second tag still exists after merge")
        
        # Verify entries have correct tag associations after merge
        entry1_tags = self.peb.db.get_entry_tags(entry1['data']['id'])
        entry2_tags = self.peb.db.get_entry_tags(entry2['data']['id'])
        
        # Entry 1 should only have the merged tag now
        self.assertEqual(len(entry1_tags), 1, "Entry 1 should have only merged tag")
        self.assertEqual(entry1_tags[0][1], merged_tag_name, 
                        "Entry 1 should have merged tag")
        
        # Entry 2 should have merged tag and tag3
        self.assertEqual(len(entry2_tags), 2, "Entry 2 should have merged tag and tag3")
        tag_names_after_merge = [tag[1] for tag in entry2_tags]
        self.assertIn(merged_tag_name, tag_names_after_merge, 
                      "Entry 2 should have merged tag")
        self.assertIn(tag_names[2], tag_names_after_merge, 
                      "Entry 2 should still have tag3")

    def test_config_edge_cases(self):
        """Test configuration edge cases"""
        # Test empty config
        empty_config = Path(self.test_dir) / 'empty_config.ini'
        empty_config.write_text("")
        os.environ['PROJEB_CONFIG'] = str(empty_config)
        with self.assertRaises(RuntimeError):
            ProjEB(api_mode=True)
        
        # Test missing sections
        partial_config = Path(self.test_dir) / 'partial_config.ini'
        partial_config.write_text("[database]\nfile=test.db")
        os.environ['PROJEB_CONFIG'] = str(partial_config)
        with self.assertRaises(RuntimeError):
            ProjEB(api_mode=True)

    def test_error_handling(self):
        """Test error handling in operations"""
        # Test nonexistent notebook ID
        entry_result = self.peb.create_entry(Args(
            notebook_id=9999,
            title='Test Entry',
            content='Test Content'
        ))
        # This should fail because notebook doesn't exist
        self.assertIsNone(entry_result.get('data'), 
                          "Entry creation should fail with nonexistent notebook")
        self.assertIn('Failed', entry_result['message'])
        
        # Create a notebook first to make later tests more reliable
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        
        # Test invalid attachment path
        entry_result = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Test Entry',
            content='Test Content',
            attachments='nonexistent.txt'
        ))
        self.assertIsNone(entry_result.get('data'), 
                          "Entry creation should fail with invalid attachment")
        self.assertIn('Failed', entry_result['message'])

    def test_transaction_handling(self):
        """Test transaction handling"""
        # Test rollback on error
        notebook_name = f"Test_Notebook_{os.urandom(4).hex()}"
        notebook = self.peb.create_notebook(Args(
            name=notebook_name,
            description='Test Description'
        ))
        
        initial_count = len(self.peb.list_notebooks(None)['data'])
        
        # Try to create notebook with same name (should fail)
        duplicate = self.peb.create_notebook(Args(
            name=notebook_name,  # Use same name to cause conflict
            description='Another Description'
        ))
        
        # Verify no partial data was saved
        final_count = len(self.peb.list_notebooks(None)['data'])
        self.assertEqual(initial_count, final_count, 
                        "Number of notebooks should not change after failed creation")
        
        # Verify original notebook is unchanged
        notebook_list = self.peb.list_notebooks(None)['data']
        matching = [n for n in notebook_list if n['Name'] == notebook_name]
        self.assertEqual(len(matching), 1, 
                        "Should find exactly one notebook with the test name")
        self.assertEqual(matching[0]['Description'], 'Test Description', 
                        "Original notebook description should be unchanged")

    def test_database_connection_errors(self):
        """Test database connection error handling"""
        # Test invalid database path
        invalid_config = Path(self.test_dir) / 'invalid_config.ini'
        config_content = f"""
[database]
file = /nonexistent/path/db.sqlite

[attachments]
dir = {str(self.dirs['attachments'])}

[backup]
dir = {str(self.dirs['backups'])}

[export]
dir = {str(self.dirs['exports'])}
"""
        invalid_config.write_text(config_content)
        os.environ['PROJEB_CONFIG'] = str(invalid_config)
        
        with self.assertRaises(Exception):
            ProjEB(api_mode=True)

    def test_attachment_error_handling(self):
        """Test attachment handling errors"""
        # Create notebook first
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        
        # Test nonexistent attachment
        entry_result = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Test Entry',
            content='Test Content',
            attachments='nonexistent.txt'
        ))
        self.assertIsNone(entry_result.get('data'))
        self.assertIn('Attachment not found', entry_result['message'])
        
        # Test invalid attachment path
        entry_result = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Test Entry 2',
            content='Test Content',
            attachments='invalid_path/attachment.txt'
        ))
        self.assertIsNone(entry_result.get('data'))
        self.assertIn('Attachment not found', entry_result['message'])

    def test_tag_relationship_cascade(self):
        """Test tag relationship cascade operations"""
        # Create notebook and entry with tags
        notebook = self.peb.create_notebook(Args(
            name=f"Test_Notebook_{os.urandom(4).hex()}",
            description='Test Description'
        ))
        
        tag_name = f"test_tag_{os.urandom(4).hex()}"
        entry = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title='Test Entry',
            content='Test Content',
            tags=tag_name
        ))
        
        # Create note with same tag
        note = self.peb.create_note(Args(
            entry_id=entry['data']['id'],
            content='Test Note',
            tags=tag_name
        ))
        
        # Get tag ID
        tag = self.peb.db.get_tag_by_name(tag_name)
        self.assertIsNotNone(tag)
        
        # Delete tag
        self.peb.db.delete_tag(tag[0])
        
        # Verify relationships are removed
        entry_tags = self.peb.db.get_entry_tags(entry['data']['id'])
        note_tags = self.peb.db.get_note_tags(note['data']['id'])
        
        self.assertEqual(len(entry_tags), 0)
        self.assertEqual(len(note_tags), 0)

    def test_search_edge_cases(self):
        """Test search functionality edge cases"""
        # Clean database first - close connection before removing
        if hasattr(self, 'peb'):
            self.peb.db.close()
            self.peb = None
            
        if self.db_file.exists():
            os.remove(self.db_file)
            
        # Create fresh ProjEB instance
        self.peb = ProjEB(api_mode=True)
        
        # Test empty search
        search_result = self.peb.search(Args(query=''))
        self.assertEqual(len(search_result['data']), 0)
        
        # Test search with special characters
        search_result = self.peb.search(Args(query='test%_[]'))
        self.assertEqual(len(search_result['data']), 0)
        
        # Test search with very long query
        search_result = self.peb.search(Args(query='a' * 1000))
        self.assertEqual(len(search_result['data']), 0)
        
        # Test search with invalid tag
        search_result = self.peb.search(Args(
            query='test',
            tag=9999
        ))
        self.assertEqual(len(search_result['data']), 0)

    def test_backup_restore_edge_cases(self):
        """Test backup/restore edge cases"""
        # Test restore with invalid backup file
        restore_result = self.peb.restore(Args(
            backup_file='nonexistent.zip'
        ))
        self.assertIn('Backup file not found', restore_result['message'])
        
        # Test restore with invalid zip file
        invalid_zip = self.dirs['backups'] / 'invalid.zip'
        invalid_zip.write_text('not a zip file')
        restore_result = self.peb.restore(Args(
            backup_file=str(invalid_zip)
        ))
        self.assertIn('failed', restore_result['message'])
        
        # Test backup to read-only directory
        readonly_dir = self.dirs['backups'] / 'readonly'
        readonly_dir.mkdir(exist_ok=True)
        
        # Store original backup directory
        old_backup_dir = self.peb.config['backup']['dir']
        
        try:
            # Make directory read-only
            if os.name == 'nt':  # Windows
                import stat
                # Remove write permissions from directory
                current_permissions = os.stat(readonly_dir).st_mode
                os.chmod(readonly_dir, current_permissions & ~stat.S_IWRITE)
                
                # Verify directory is actually read-only
                if os.access(readonly_dir, os.W_OK):
                    self.skipTest("Could not make directory read-only on Windows")
            else:
                os.chmod(readonly_dir, 0o444)
            
            # Configure backup directory
            self.peb.config['backup']['dir'] = str(readonly_dir)
            
            # Attempt backup to read-only directory
            backup_result = self.peb.backup(Args())
            self.assertIn('not writable', backup_result['message'])
            
        finally:
            # Restore permissions and configuration
            if os.name == 'nt':  # Windows
                os.chmod(readonly_dir, stat.S_IWRITE | stat.S_IREAD)
            else:
                os.chmod(readonly_dir, 0o777)
            # Restore original backup directory
            self.peb.config['backup']['dir'] = old_backup_dir

    def test_import_export_edge_cases(self):
        """Test import/export edge cases"""
        # Test import with invalid JSON file
        invalid_json = self.dirs['exports'] / 'invalid.json'
        invalid_json.write_text('not a json file')
        import_result = self.peb.import_data(Args(
            file=str(invalid_json)
        ))
        self.assertIn('failed', import_result['message'])
        
        # Test import with missing required fields
        invalid_data = self.dirs['exports'] / 'missing_fields.json'
        invalid_data.write_text('{}')
        
        import_result = self.peb.import_data(Args(
            file=str(invalid_data)
        ))
        self.assertIn('successfully', import_result['message'])
        
        # Test export to read-only directory
        readonly_dir = self.dirs['exports'] / 'readonly'
        readonly_dir.mkdir(exist_ok=True)
        
        # Store original export directory
        old_export_dir = self.peb.config['export']['dir']
        
        try:
            # Make directory read-only
            if os.name == 'nt':  # Windows
                import stat
                # Remove write permissions from directory
                current_permissions = os.stat(readonly_dir).st_mode
                os.chmod(readonly_dir, current_permissions & ~stat.S_IWRITE)
                
                # Verify directory is actually read-only
                if os.access(readonly_dir, os.W_OK):
                    self.skipTest("Could not make directory read-only on Windows")
            else:
                os.chmod(readonly_dir, 0o444)
            
            # Configure export directory
            self.peb.config['export']['dir'] = str(readonly_dir)
            
            # Attempt export to read-only directory
            export_result = self.peb.export_data(Args())
            self.assertIn('not writable', export_result['message'])
            
        finally:
            # Restore permissions and configuration
            if os.name == 'nt':  # Windows
                os.chmod(readonly_dir, stat.S_IWRITE | stat.S_IREAD)
            else:
                os.chmod(readonly_dir, 0o777)
            # Restore original export directory
            self.peb.config['export']['dir'] = old_export_dir

    def verify_readonly(self, path):
        """Verify a path is actually read-only"""
        test_file = path / 'test.txt'
        with self.assertRaises((PermissionError, OSError)):
            test_file.write_text('test')

def make_readonly(path):
    """Make a directory read-only in a cross-platform way"""
    if os.name == 'nt':  # Windows
        os.system(f'attrib +R "{path}"')
    else:
        os.chmod(path, 0o444)

def make_writable(path):
    """Make a directory writable in a cross-platform way"""
    if os.name == 'nt':  # Windows
        os.system(f'attrib -R "{path}"')
    else:
        os.chmod(path, 0o777)

def test_database_operations_errors(self):
    """Test database operations error handling"""
    # Test invalid SQL
    with self.assertRaises(sqlite3.Error):
        self.peb.db.conn.execute("INVALID SQL")
    
    # Test duplicate constraint violations
    notebook = self.peb.create_notebook(Args(
        name="Test_Notebook",
        description="Test"
    ))
    self.assertIsNotNone(notebook.get('data'))
    
    # Try creating same notebook again
    duplicate = self.peb.create_notebook(Args(
        name="Test_Notebook",
        description="Test"
    ))
    self.assertIsNone(duplicate.get('data'))
    
    # Test invalid foreign key
    invalid_entry = self.peb.create_entry(Args(
        notebook_id=999999,
        title="Test Entry",
        content="Test"
    ))
    self.assertIsNone(invalid_entry.get('data'))

    def test_import_export_errors(self):
        """Test import/export error handling"""
        # Test export with invalid directory permissions
        export_dir = self.dirs['exports']
        os.chmod(export_dir, 0o444)  # Read-only
        
        try:
            result = self.peb.export_data(Args())
            self.assertIn('failed', result['message'].lower())
        finally:
            os.chmod(export_dir, 0o777)  # Restore permissions
        
        # Test import with invalid JSON
        invalid_json = self.dirs['exports'] / 'invalid.json'
        invalid_json.write_text('{"invalid": json}')
        
        result = self.peb.import_data(Args(file=str(invalid_json)))
        self.assertIn('failed', result['message'].lower())
        
        # Test import with missing required data
        empty_json = self.dirs['exports'] / 'empty.json'
        empty_json.write_text('{}')
        
        result = self.peb.import_data(Args(file=str(empty_json)))
        self.assertIn('successfully', result['message'])

    def test_attachment_operations(self):
        """Test attachment operations and error handling"""
        # Create test files
        valid_file = self.dirs['attachments'] / 'valid.txt'
        valid_file.write_text('Valid content')
        
        # Test valid attachment
        notebook = self.peb.create_notebook(Args(
            name="Test_Notebook",
            description="Test"
        ))
        
        entry = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title="Test Entry",
            content="Test",
            attachments=str(valid_file)
        ))
        self.assertIsNotNone(entry.get('data'))
        
        # Verify attachment was stored
        attachments = self.peb.db.get_attachments(entry_id=entry['data']['id'])
        self.assertEqual(len(attachments), 1)
        
        # Test invalid attachment path
        invalid_entry = self.peb.create_entry(Args(
            notebook_id=notebook['data']['id'],
            title="Invalid Entry",
            content="Test",
            attachments="nonexistent.txt"
        ))
        self.assertIsNone(invalid_entry.get('data'))

    def any_test_creating_entry(self):
        # Create notebook
        notebook_name = f"Test_Notebook_{os.urandom(4).hex()}"
        notebook = self.peb.create_notebook(Args(
            name=notebook_name,
            description='Test Description'
        ))
        
        # Create entry using notebook name
        entry = self.peb.create_entry(Args(
            notebook=notebook_name,  # Use name instead of ID
            title='Test Entry',
            content='Test Content'
            # ... other args as needed
        ))

if __name__ == '__main__':
    unittest.main()