import unittest
import os
import subprocess
import tempfile
import shutil  # Add this import
from pathlib import Path
import time

class TestUsePebBatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment"""
        cls.original_config = os.environ.get('PROJEB_CONFIG', None)
        cls.batch_file = Path('use_peb.bat')
        
        # Verify batch file exists
        if not cls.batch_file.exists():
            raise FileNotFoundError("use_peb.bat not found")

    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create local test directories with absolute paths
        self.test_dir = Path.cwd() / 'test_data'
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        
        self.db_file = self.test_dir / "test.db"
        
        # Create test directories with absolute paths
        self.dirs = {
            'attachments': self.test_dir / 'attachments',
            'backups': self.test_dir / 'backups',
            'exports': self.test_dir / 'exports'
        }
        
        # Create directories
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Create test configuration
        self.config_path = self.test_dir / 'test_config.ini'
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

    def tearDown(self):
        """Clean up after each test"""
        try:
            # Close any open file handles
            time.sleep(0.1)  # Give time for handles to close
            
            # Remove test directory and all contents
            if self.test_dir.exists():
                # Force close any SQLite connections
                try:
                    import sqlite3
                    if self.db_file.exists():
                        conn = sqlite3.connect(self.db_file)
                        conn.close()
                except:
                    pass
                    
                # Remove directory with retries
                max_retries = 3
                for i in range(max_retries):
                    try:
                        shutil.rmtree(self.test_dir, ignore_errors=True)
                        break
                    except PermissionError:
                        time.sleep(0.5)
                        continue
                        
        finally:
            # Restore original config
            if self.original_config:
                os.environ['PROJEB_CONFIG'] = self.original_config
            else:
                os.environ.pop('PROJEB_CONFIG', None)

    def run_batch_command(self, command):
        """Helper method to run batch file commands"""
        try:
            # Split the command into parts to avoid shell interpretation issues
            cmd_parts = ['python', 'peb.py'] + command.split()
            
            # Add environment variables
            env = os.environ.copy()
            env['PROJEB_CONFIG'] = str(self.config_path)
            
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=10,  # Increased timeout
                env=env,
                cwd=os.path.dirname(os.path.abspath(__file__))  # Set working directory
            )
            return result
        except subprocess.TimeoutExpired:
            self.fail(f"Command timed out: {command}")
        except Exception as e:
            self.fail(f"Command failed: {str(e)}")

    def test_notebook_creation(self):
        """Test notebook creation command"""
        result = self.run_batch_command(
            'create-notebook --name "TestNotebook" --description "TestDescription"'
        )
        self.assertEqual(result.returncode, 0, 
                        f"Command failed with stderr: {result.stderr}")
        self.assertIn("Notebook created successfully", result.stdout)

    def test_entry_creation(self):
        """Test entry creation command"""
        # Create notebook first
        notebook_result = self.run_batch_command(
            'create-notebook --name "TestNotebook" --description "TestDescription"'
        )
        self.assertEqual(notebook_result.returncode, 0, 
                        f"Notebook creation failed: {notebook_result.stderr}")
        
        # Create entry
        entry_result = self.run_batch_command(
            'create-entry --notebook-id 1 --title "TestEntry" --content "TestContent"'
        )
        self.assertEqual(entry_result.returncode, 0, 
                        f"Entry creation failed: {entry_result.stderr}")
        self.assertIn("Entry created successfully", entry_result.stdout)

    def test_note_creation(self):
        """Test note creation command"""
        # Create notebook and entry first
        self.run_batch_command(
            'create-notebook --name "TestNotebook" --description "TestDescription"'
        )
        self.run_batch_command(
            'create-entry --notebook-id 1 --title "TestEntry" --content "TestContent"'
        )
        
        # Create note
        note_result = self.run_batch_command(
            'create-note --entry-id 1 --content "TestNoteContent"'
        )
        self.assertEqual(note_result.returncode, 0, 
                        f"Note creation failed: {note_result.stderr}")
        self.assertIn("Note created successfully", note_result.stdout)

    def test_search_functionality(self):
        """Test search command"""
        # Create test data
        self.run_batch_command(
            'create-notebook --name "TestNotebook" --description "TestDescription"'
        )
        self.run_batch_command(
            'create-entry --notebook-id 1 --title "TestEntry" --content "UniqueSearchContent"'
        )
        
        # Search for unique content
        search_result = self.run_batch_command(
            'search --query "UniqueSearchContent"'
        )
        self.assertEqual(search_result.returncode, 0,
                        f"Search failed: {search_result.stderr}")
        self.assertIn("UniqueSearchContent", search_result.stdout)

    def test_tag_management(self):
        """Test tag management commands"""
        # Create notebook and entry with tags
        self.run_batch_command(
            'create-notebook --name "TestNotebook" --description "TestDescription"'
        )
        
        # Create entry with tags
        entry_result = self.run_batch_command(
            'create-entry --notebook-id 1 --title "TestEntry" --content "TestContent" --tags "testtag1,testtag2"'
        )
        self.assertEqual(entry_result.returncode, 0,
                        f"Entry creation failed: {entry_result.stderr}")
        
        # List tags to verify creation
        list_result = self.run_batch_command('list-tags')
        self.assertEqual(list_result.returncode, 0,
                        f"Tag listing failed: {list_result.stderr}")
        self.assertIn("testtag1", list_result.stdout)
        self.assertIn("testtag2", list_result.stdout)
        
        # Merge tags
        merge_result = self.run_batch_command(
            'merge-tags --tags 1,2 --new-tag merged_tag'
        )
        self.assertEqual(merge_result.returncode, 0,
                        f"Tag merge failed: {merge_result.stderr}")
        self.assertIn("Tags merged successfully", merge_result.stdout)
        
        # Verify merged tag exists and old tags are gone
        final_list = self.run_batch_command('list-tags')
        self.assertEqual(final_list.returncode, 0)
        self.assertIn("merged_tag", final_list.stdout)
        self.assertNotIn("testtag1", final_list.stdout)
        self.assertNotIn("testtag2", final_list.stdout)

    def test_list_notebooks(self):
        """Test notebook listing command"""
        # Create a notebook
        self.run_batch_command(
            'create-notebook --name "TestNotebook" --description "TestDescription"'
        )
        
        # List notebooks
        list_result = self.run_batch_command('list-notebooks')
        self.assertEqual(list_result.returncode, 0,
                        f"Listing notebooks failed: {list_result.stderr}")
        self.assertIn("TestNotebook", list_result.stdout)

    def test_list_notes(self):
        """Test note listing command"""
        # Create test data
        self.run_batch_command(
            'create-notebook --name "TestNotebook" --description "TestDescription"'
        )
        self.run_batch_command(
            'create-entry --notebook-id 1 --title "TestEntry" --content "TestContent"'
        )
        self.run_batch_command(
            'create-note --entry-id 1 --content "TestNoteContent"'
        )
        
        # List notes
        list_result = self.run_batch_command('list-notes --entry-id 1')
        self.assertEqual(list_result.returncode, 0,
                        f"Listing notes failed: {list_result.stderr}")
        self.assertIn("TestNoteContent", list_result.stdout)

    def test_backup_restore(self):
        """Test backup and restore functionality"""
        # Create test data
        self.run_batch_command(
            'create-notebook --name "TestNotebook" --description "TestDescription"'
        )
        self.run_batch_command(
            'create-entry --notebook-id 1 --title "TestEntry" --content "TestContent"'
        )
        
        # Create backup
        backup_result = self.run_batch_command('backup')
        self.assertEqual(backup_result.returncode, 0,
                        f"Backup failed with stderr: {backup_result.stderr}")
        self.assertIn("Backup created at", backup_result.stdout)
        
        # Get backup file path from output
        backup_file = None
        for line in backup_result.stdout.splitlines():
            if "Backup created at" in line:
                backup_file = Path(line.split("at")[-1].strip())
                backup_file = self.dirs['backups'] / backup_file.name
                break
        
        self.assertIsNotNone(backup_file, "Backup file path not found in output")
        self.assertTrue(backup_file.exists(), f"Backup file not found at {backup_file}")
        
        # Store original database content
        original_notebooks = self.run_batch_command('list-notebooks')
        
        # Clean up existing data
        try:
            if self.db_file.exists():
                self.db_file.unlink()
        except FileNotFoundError:
            pass
        
        self.assertFalse(self.db_file.exists(), "Database file still exists after removal")
        
        # Restore from backup - use raw string for path
        restore_cmd = f'restore --backup-file {backup_file}'
        restore_result = self.run_batch_command(restore_cmd)
        self.assertEqual(restore_result.returncode, 0,
                        f"Restore failed with stderr: {restore_result.stderr}")
        self.assertIn("Restore completed successfully", restore_result.stdout)
        
        # Verify restored data
        restored_notebooks = self.run_batch_command('list-notebooks')
        self.assertEqual(restored_notebooks.stdout, original_notebooks.stdout,
                        "Restored data doesn't match original")

    def test_export_import(self):
        """Test export and import functionality"""
        # Create test data
        self.run_batch_command(
            'create-notebook --name "TestNotebook" --description "TestDescription"'
        )
        self.run_batch_command(
            'create-entry --notebook-id 1 --title "TestEntry" --content "TestContent"'
        )
        
        # Export data
        export_result = self.run_batch_command('export')
        self.assertEqual(export_result.returncode, 0,
                        f"Export failed: {export_result.stderr}")
        self.assertIn("Data exported to", export_result.stdout)
        
        # Get export file path
        export_file = None
        for line in export_result.stdout.splitlines():
            if "Data exported to" in line:
                export_file = line.split("to")[-1].strip()
                break
                
        self.assertIsNotNone(export_file, "Export file path not found in output")
        
        # Clean up existing data
        os.remove(self.db_file)
        
        # Import data - using normalized path without quotes
        import_result = self.run_batch_command(f'import --file {export_file}')
        self.assertEqual(import_result.returncode, 0,
                        f"Import failed: {import_result.stderr}")
        self.assertIn("Data imported successfully", import_result.stdout)

if __name__ == '__main__':
    unittest.main()