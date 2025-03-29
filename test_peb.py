import os
import unittest
import sqlite3
import configparser
import shutil
import database
from peb import initialize_database, create_notebook_command, create_entry_command, list_entries_command, read_entry_command, create_note_command, search_entries_by_tag_command, search_notes_by_tag_command

class TestProjEB(unittest.TestCase):

    def setUp(self):
        # Set up a test database
        self.test_db = "test_project_binder.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.conn = sqlite3.connect(self.test_db)
        database.create_database(self.conn)
        
        # Update configuration file to use the test database
        config = configparser.ConfigParser()
        config['database'] = {'file': self.test_db}
        with open('configuration.ini', 'w') as configfile:
            config.write(configfile)
        
        # Set the global DATABASE_FILE in database.py
        database.DATABASE_FILE = self.test_db

    def tearDown(self):
        self.conn.close()
        os.remove(self.test_db)

    def test_create_notebook(self):
        message = create_notebook_command(self.conn, "Test Notebook", api=True)
        self.assertEqual(message, "Notebook 'Test Notebook' created successfully.")
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM notebooks WHERE name = ?', ("Test Notebook",))
        notebook = cursor.fetchone()
        self.assertIsNotNone(notebook)
        self.assertEqual(notebook[0], "Test Notebook")

    def test_create_entry(self):
        create_notebook_command(self.conn, "Test Notebook", api=True)
        messages = create_entry_command(self.conn, "Test Entry", "This is a test entry.", "Test Notebook", api=True)
        self.assertIn("Entry 'Test Entry' created successfully.", messages)
        cursor = self.conn.cursor()
        cursor.execute('SELECT title, content, timestamp FROM entries WHERE title = ?', ("Test Entry",))
        entry = cursor.fetchone()
        self.assertIsNotNone(entry)
        self.assertEqual(entry[0], "Test Entry")
        self.assertEqual(entry[1], "This is a test entry.")

    def test_create_entry_without_notebook(self):
        messages = create_entry_command(self.conn, "Test Entry Without Notebook", "This is a test entry without a notebook.", api=True)
        self.assertIn("Entry 'Test Entry Without Notebook' created successfully.", messages)
        cursor = self.conn.cursor()
        cursor.execute('SELECT title, content, timestamp FROM entries WHERE title = ?', ("Test Entry Without Notebook",))
        entry = cursor.fetchone()
        self.assertIsNotNone(entry)
        self.assertEqual(entry[0], "Test Entry Without Notebook")
        self.assertEqual(entry[1], "This is a test entry without a notebook.")

    def test_list_entries(self):
        create_notebook_command(self.conn, "Test Notebook 1", api=True)
        create_notebook_command(self.conn, "Test Notebook 2", api=True)
        create_entry_command(self.conn, "Test Entry 1", "This is the first test entry.", "Test Notebook 1", api=True)
        create_entry_command(self.conn, "Test Entry 2", "This is the second test entry.", "Test Notebook 1", api=True)
        entries = list_entries_command(self.conn, api=True)
        self.assertEqual(len(entries), 2)

    def test_read_entry(self):
        create_notebook_command(self.conn, "Test Notebook", api=True)
        create_entry_command(self.conn, "Test Entry", "This is a test entry.", "Test Notebook", api=True)
        entry = read_entry_command(self.conn, "Test Entry", api=True)
        self.assertIsNotNone(entry)
        self.assertEqual(entry[0], "Test Entry")
        self.assertEqual(entry[1], "This is a test entry.")

    def test_create_note_with_tags(self):
        create_notebook_command(self.conn, "Test Notebook", api=True)
        create_entry_command(self.conn, "Test Entry", "This is a test entry.", "Test Notebook", ["tag1", "tag2"], api=True)
        message = create_note_command(self.conn, "Test Entry", "This is a test note with tags.", ["tag2", "tag3"], api=True)
        self.assertEqual(message, "Note added successfully.")
        cursor = self.conn.cursor()
        cursor.execute('SELECT content FROM notes WHERE content = ?', ("This is a test note with tags.",))
        note = cursor.fetchone()
        self.assertIsNotNone(note)
        self.assertEqual(note[0], "This is a test note with tags.")

    def test_search_entries_by_tag(self):
        create_notebook_command(self.conn, "Test Notebook", api=True)
        create_entry_command(self.conn, "Test Entry", "This is a test entry with tag.", "Test Notebook", ["tag1"], api=True)
        entries = search_entries_by_tag_command(self.conn, "tag1", api=True)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][1], "Test Entry")

    def test_search_notes_by_tag(self):
        create_notebook_command(self.conn, "Test Notebook", api=True)
        create_entry_command(self.conn, "Test Entry", "This is a test entry.", "Test Notebook", ["tag1"], api=True)
        create_note_command(self.conn, "Test Entry", "This is a test note with tag.", ["tag2"], api=True)
        notes = search_notes_by_tag_command(self.conn, "tag2", api=True)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0][1], "This is a test note with tag.")

if __name__ == "__main__":
    unittest.main()