import sqlite3
import os
import datetime
import uuid
from pathlib import Path

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.create_database()

    def connect(self):
        """Create a database connection."""
        try:
            self.conn = sqlite3.connect(self.db_file)
            return self.conn
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return None

    def create_database(self):
        """Create database tables if they don't exist."""
        sql_create_notebooks = """
        CREATE TABLE IF NOT EXISTS notebooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'active'
        );"""

        sql_create_entries = """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notebook_id INTEGER,
            title TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (notebook_id) REFERENCES notebooks (id),
            UNIQUE(notebook_id, title)
        );"""

        sql_create_notes = """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES entries (id)
        );"""

        sql_create_tags = """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        );"""

        sql_create_attachments = """
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            entry_id INTEGER,
            note_id INTEGER,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES entries (id),
            FOREIGN KEY (note_id) REFERENCES notes (id)
        );"""

        sql_create_entry_tags = """
        CREATE TABLE IF NOT EXISTS entry_tags (
            entry_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (entry_id) REFERENCES entries (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id),
            PRIMARY KEY (entry_id, tag_id)
        );"""

        sql_create_note_tags = """
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (note_id) REFERENCES notes (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id),
            PRIMARY KEY (note_id, tag_id)
        );"""

        conn = self.connect()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute(sql_create_notebooks)
                c.execute(sql_create_entries)
                c.execute(sql_create_notes)
                c.execute(sql_create_tags)
                c.execute(sql_create_attachments)
                c.execute(sql_create_entry_tags)
                c.execute(sql_create_note_tags)
                conn.commit()
            except sqlite3.Error as e:
                print(f"Error creating database tables: {e}")
        else:
            print("Error: Cannot create database connection.")

    def create_notebook(self, name, description=""):
        """Create a new notebook."""
        sql = """INSERT INTO notebooks(name, description, created_at)
                 VALUES(?, ?, ?)"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (name, description, datetime.datetime.now()))
            notebook_id = cur.lastrowid
            conn.commit()
            return notebook_id
        except sqlite3.Error as e:
            print(f"Error creating notebook: {e}")
            return None

    def get_notebooks(self):
        """Get all notebooks."""
        sql = """SELECT id, name, description, created_at, status 
                 FROM notebooks ORDER BY created_at DESC"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting notebooks: {e}")
            return []

    def create_entry(self, notebook_id, title, content="", attachments=None):
        """Create a new entry in a notebook."""
        sql = """INSERT INTO entries(notebook_id, title, content, created_at)
                 VALUES(?, ?, ?, ?)"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (notebook_id, title, content, datetime.datetime.now()))
            entry_id = cur.lastrowid
            
            if attachments:
                for attachment in attachments:
                    self.add_attachment(entry_id, None, attachment)
                    
            conn.commit()
            return entry_id
        except sqlite3.Error as e:
            print(f"Error creating entry: {e}")
            return None

    def add_attachment(self, entry_id, note_id, file_path):
        """Add an attachment to an entry or note."""
        stored_name = f"{uuid.uuid4()}{Path(file_path).suffix}"
        sql = """INSERT INTO attachments(original_name, stored_name, entry_id, 
                 note_id, created_at) VALUES(?, ?, ?, ?, ?)"""
        
        try:
            cur = self.conn.cursor()
            cur.execute(sql, (Path(file_path).name, stored_name, entry_id, 
                            note_id, datetime.datetime.now()))
            self.conn.commit()
            return stored_name
        except sqlite3.Error as e:
            print(f"Error adding attachment: {e}")
            return None

    def create_note(self, entry_id, content, attachments=None):
        """Create a new note for an entry."""
        sql = """INSERT INTO notes(entry_id, content, created_at)
                 VALUES(?, ?, ?)"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (entry_id, content, datetime.datetime.now()))
            note_id = cur.lastrowid
            
            if attachments:
                for attachment in attachments:
                    self.add_attachment(None, note_id, attachment)
                    
            conn.commit()
            return note_id
        except sqlite3.Error as e:
            print(f"Error creating note: {e}")
            return None

    def create_tag(self, name, description=""):
        """Create a new tag."""
        sql = """INSERT INTO tags(name, description)
                 VALUES(?, ?)"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (name, description))
            conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating tag: {e}")
            return None

    def add_tag_to_entry(self, entry_id, tag_id):
        """Add a tag to an entry."""
        sql = """INSERT INTO entry_tags(entry_id, tag_id)
                 VALUES(?, ?)"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (entry_id, tag_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding tag to entry: {e}")
            return False

    def add_tag_to_note(self, note_id, tag_id):
        """Add a tag to a note."""
        sql = """INSERT INTO note_tags(note_id, tag_id)
                 VALUES(?, ?)"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (note_id, tag_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding tag to note: {e}")
            return False

    def get_tags(self):
        """Get all tags."""
        sql = """SELECT id, name, description 
                 FROM tags 
                 ORDER BY name"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting tags: {e}")
            return []

    def get_entry_tags(self, entry_id):
        """Get all tags for an entry."""
        sql = """SELECT t.id, t.name, t.description 
                 FROM tags t
                 JOIN entry_tags et ON t.id = et.tag_id
                 WHERE et.entry_id = ?
                 ORDER BY t.name"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (entry_id,))
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting entry tags: {e}")
            return []

    def get_note_tags(self, note_id):
        """Get all tags for a note."""
        sql = """SELECT t.id, t.name, t.description 
                 FROM tags t
                 JOIN note_tags nt ON t.id = nt.tag_id
                 WHERE nt.note_id = ?
                 ORDER BY t.name"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (note_id,))
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting note tags: {e}")
            return []

    def search_by_tag(self, tag_id):
        """Search entries and notes by tag."""
        sql_entries = """SELECT DISTINCT e.* 
                        FROM entries e
                        JOIN entry_tags et ON e.id = et.entry_id
                        WHERE et.tag_id = ?"""
        sql_notes = """SELECT DISTINCT n.* 
                      FROM notes n
                      JOIN note_tags nt ON n.id = nt.note_id
                      WHERE nt.tag_id = ?"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            # Get tagged entries
            cur.execute(sql_entries, (tag_id,))
            entries = cur.fetchall()
            
            # Get tagged notes
            cur.execute(sql_notes, (tag_id,))
            notes = cur.fetchall()
            
            return {'entries': entries, 'notes': notes}
        except sqlite3.Error as e:
            print(f"Error searching by tag: {e}")
            return {'entries': [], 'notes': []}

    def get_entries(self, notebook_id=None, tag_id=None):
        """Get entries with optional filters."""
        if notebook_id and tag_id:
            sql = """SELECT DISTINCT e.* FROM entries e
                     JOIN entry_tags et ON e.id = et.entry_id
                     WHERE e.notebook_id = ? AND et.tag_id = ?
                     ORDER BY e.created_at DESC"""
            params = (notebook_id, tag_id)
        elif notebook_id:
            sql = """SELECT * FROM entries
                     WHERE notebook_id = ?
                     ORDER BY created_at DESC"""
            params = (notebook_id,)
        elif tag_id:
            sql = """SELECT DISTINCT e.* FROM entries e
                     JOIN entry_tags et ON e.id = et.entry_id
                     WHERE et.tag_id = ?
                     ORDER BY e.created_at DESC"""
            params = (tag_id,)
        else:
            sql = "SELECT * FROM entries ORDER BY created_at DESC"
            params = ()

        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting entries: {e}")
            return []

    def get_notes(self, entry_id):
        """Get all notes for an entry."""
        sql = """SELECT * FROM notes
                 WHERE entry_id = ?
                 ORDER BY created_at DESC"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (entry_id,))
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting notes: {e}")
            return []

    def search(self, query, tag_id=None):
        """Search entries and notes by content"""
        if tag_id:
            sql = """SELECT DISTINCT e.id, e.notebook_id, e.title, e.content, e.created_at 
                     FROM entries e
                     LEFT JOIN entry_tags et ON e.id = et.entry_id
                     WHERE (e.title LIKE ? OR e.content LIKE ?)
                     AND et.tag_id = ?
                     ORDER BY created_at DESC"""
            params = (f"%{query}%", f"%{query}%", tag_id)
        else:
            sql = """SELECT id, notebook_id, title, content, created_at 
                     FROM entries
                     WHERE title LIKE ? OR content LIKE ?
                     ORDER BY created_at DESC"""
            params = (f"%{query}%", f"%{query}%")

        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error searching: {e}")
            return []

    def merge_tags(self, old_tag_ids, new_tag_name):
        """Merge multiple tags into a new tag."""
        conn = self.connect()
        try:
            # Create new tag
            cur = conn.cursor()
            cur.execute("INSERT INTO tags (name) VALUES (?)", (new_tag_name,))
            new_tag_id = cur.lastrowid

            # Update entry tags
            cur.execute("""
                INSERT INTO entry_tags (entry_id, tag_id)
                SELECT DISTINCT entry_id, ? 
                FROM entry_tags 
                WHERE tag_id IN ({})
            """.format(','.join('?' * len(old_tag_ids))), 
            (new_tag_id, *old_tag_ids))

            # Update note tags
            cur.execute("""
                INSERT INTO note_tags (note_id, tag_id)
                SELECT DISTINCT note_id, ? 
                FROM note_tags 
                WHERE tag_id IN ({})
            """.format(','.join('?' * len(old_tag_ids))), 
            (new_tag_id, *old_tag_ids))

            # Delete old tags
            cur.execute("""
                DELETE FROM tags 
                WHERE id IN ({})
            """.format(','.join('?' * len(old_tag_ids))), 
            old_tag_ids)

            conn.commit()
            return new_tag_id
        except sqlite3.Error as e:
            print(f"Error merging tags: {e}")
            return None

    def update_notebook_status(self, notebook_id, status):
        """Update notebook status (active/archived)."""
        sql = """UPDATE notebooks 
                 SET status = ?
                 WHERE id = ?"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (status, notebook_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating notebook status: {e}")
            return False

    def rename_tag(self, tag_id, new_name):
        """Rename a tag."""
        sql = """UPDATE tags 
                 SET name = ?
                 WHERE id = ?"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (new_name, tag_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error renaming tag: {e}")
            return False

    def delete_tag(self, tag_id):
        """Delete a tag and its relationships."""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM entry_tags WHERE tag_id = ?", (tag_id,))
            cur.execute("DELETE FROM note_tags WHERE tag_id = ?", (tag_id,))
            cur.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting tag: {e}")
            return False

    def get_notebook_by_name(self, name):
        """Get notebook by name."""
        sql = """SELECT * FROM notebooks
                 WHERE name = ?"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (name,))
            return cur.fetchone()
        except sqlite3.Error as e:
            print(f"Error getting notebook: {e}")
            return None

    def get_entry_by_title(self, notebook_id, title):
        """Get entry by title within a notebook."""
        sql = """SELECT * FROM entries
                 WHERE notebook_id = ? AND title = ?"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (notebook_id, title))
            return cur.fetchone()
        except sqlite3.Error as e:
            print(f"Error getting entry: {e}")
            return None

    def get_attachments(self, entry_id=None, note_id=None):
        """Get attachments for an entry or note."""
        if entry_id:
            sql = """SELECT * FROM attachments
                     WHERE entry_id = ?
                     ORDER BY created_at DESC"""
            params = (entry_id,)
        else:
            sql = """SELECT * FROM attachments
                     WHERE note_id = ?
                     ORDER BY created_at DESC"""
            params = (note_id,)
            
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting attachments: {e}")
            return []

    def get_tag_by_name(self, name):
        """Get tag by name."""
        sql = """SELECT * FROM tags
                 WHERE name = ?"""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (name,))
            return cur.fetchone()
        except sqlite3.Error as e:
            print(f"Error getting tag: {e}")
            return None

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()