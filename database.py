import sqlite3
import shutil
import os
from datetime import datetime

# Database file from configuration
DATABASE_FILE = None

# Directory to store attachments
ATTACHMENTS_DIR = None

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

def create_database(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            attachment_path TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notebooks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            state TEXT NOT NULL DEFAULT 'active'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entry_notebook (
            entry_id INTEGER,
            notebook_id INTEGER,
            PRIMARY KEY (entry_id, notebook_id),
            FOREIGN KEY (entry_id) REFERENCES entries(id),
            FOREIGN KEY (notebook_id) REFERENCES notebooks(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            entry_id INTEGER,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            attachment_path TEXT,
            FOREIGN KEY (entry_id) REFERENCES entries(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entry_tags (
            entry_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (entry_id, tag_id),
            FOREIGN KEY (entry_id) REFERENCES entries(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (note_id, tag_id),
            FOREIGN KEY (note_id) REFERENCES notes(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY,
            operation TEXT NOT NULL,
            table_name TEXT NOT NULL,
            item_id INTEGER,
            timestamp TEXT NOT NULL,
            details TEXT
        )
    ''')
    conn.commit()
    if not os.path.exists(ATTACHMENTS_DIR):
        os.makedirs(ATTACHMENTS_DIR)

def log_operation(conn, operation, table_name, item_id=None, details=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (operation, table_name, item_id, timestamp, details)
        VALUES (?, ?, ?, ?, ?)
    ''', (operation, table_name, item_id, timestamp, details))
    conn.commit()

def create_notebook(conn, name):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO notebooks (name)
            VALUES (?)
        ''', (name,))
        conn.commit()
        log_operation(conn, 'CREATE_NOTEBOOK', 'notebooks', cursor.lastrowid, f"Notebook '{name}' created.")
        return f"Notebook '{name}' created successfully."
    except sqlite3.IntegrityError:
        log_operation(conn, 'CREATE_NOTEBOOK_FAILED', 'notebooks', details=f"Notebook '{name}' already exists.")
        return f"Notebook '{name}' already exists."

def add_tags(conn, table, item_id, tags):
    cursor = conn.cursor()
    if tags is None:
        tags = []
    for tag in tags:
        cursor.execute('SELECT id FROM tags WHERE name = ?', (tag,))
        tag_id = cursor.fetchone()
        if not tag_id:
            cursor.execute('INSERT INTO tags (name) VALUES (?)', (tag,))
            tag_id = cursor.lastrowid
        else:
            tag_id = tag_id[0]
        cursor.execute(f'INSERT OR IGNORE INTO {table}_tags ({table}_id, tag_id) VALUES (?, ?)', (item_id, tag_id))
        log_operation(conn, 'ADD_TAG', table, item_id, f"Tag '{tag}' added.")
    conn.commit()

def create_entry(conn, title, content, notebooks, file_path=None, tags=[]):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor = conn.cursor()
    for notebook in notebooks:
        cursor.execute('SELECT state FROM notebooks WHERE name = ?', (notebook,))
        state = cursor.fetchone()
        if state and state[0] != 'active':
            log_operation(conn, 'CREATE_ENTRY', 'entries', details=f"Cannot add entry to archived notebook '{notebook}'.")
            return [f"Cannot add entry to archived notebook '{notebook}'."]
    
    attachment_path = None
    if file_path:
        attachment_path = save_attachment(file_path)

    cursor.execute('''
        INSERT INTO entries (title, content, timestamp, attachment_path)
        VALUES (?, ?, ?, ?)
    ''', (title, content, timestamp, attachment_path))
    entry_id = cursor.lastrowid
    log_operation(conn, 'CREATE_ENTRY', 'entries', entry_id, f"Entry '{title}' created.")
    
    messages = []
    if notebooks:
        for notebook in notebooks:
            cursor.execute('SELECT id FROM notebooks WHERE name = ?', (notebook,))
            notebook_id = cursor.fetchone()
            if notebook_id:
                cursor.execute('''
                    INSERT INTO entry_notebook (entry_id, notebook_id)
                    VALUES (?, ?)
                ''', (entry_id, notebook_id[0]))
                log_operation(conn, 'TAG_ENTRY', 'entries', entry_id, f"Entry tagged to notebook '{notebook}'.")
            else:
                messages.append(f"Notebook '{notebook}' does not exist. Entry not tagged to this notebook.")
                log_operation(conn, 'TAG_ENTRY_FAILED', 'entries', entry_id, f"Notebook '{notebook}' does not exist.")
    
    add_tags(conn, 'entry', entry_id, tags)
    
    conn.commit()
    messages.append(f"Entry '{title}' created successfully.")
    return messages

def create_note_for_entry(conn, entry_title, note_content, file_path=None, tags=[]):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM entries WHERE title = ?', (entry_title,))
    entry_id = cursor.fetchone()
    if entry_id:
        attachment_path = None
        if file_path:
            attachment_path = save_attachment(file_path)

        cursor.execute('''
            INSERT INTO notes (entry_id, content, timestamp, attachment_path)
            VALUES (?, ?, ?, ?)
        ''', (entry_id[0], note_content, timestamp, attachment_path))
        note_id = cursor.lastrowid
        log_operation(conn, 'CREATE_NOTE', 'notes', note_id, f"Note for entry '{entry_title}' created.")
        
        add_tags(conn, 'note', note_id, tags)
        
        conn.commit()
        return "Note added successfully."
    else:
        log_operation(conn, 'CREATE_NOTE_FAILED', 'notes', details=f"Entry with title '{entry_title}' does not exist.")
        return f"Entry with title '{entry_title}' does not exist."

def save_attachment(file_path):
    attachment_path = os.path.join(ATTACHMENTS_DIR, os.path.basename(file_path))
    shutil.copy(file_path, attachment_path)
    return attachment_path

def list_entries(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.id, e.title, e.timestamp, GROUP_CONCAT(n.name, ', ') as notebooks
        FROM entries e
        LEFT JOIN entry_notebook en ON e.id = en.entry_id
        LEFT JOIN notebooks n ON en.notebook_id = n.id
        GROUP BY e.id
    ''')
    entries = cursor.fetchall()
    log_operation(conn, 'LIST_ENTRIES', 'entries')
    return entries

def read_entry_by_title(conn, title):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.title, e.content, e.timestamp, GROUP_CONCAT(n.name, ', ') as notebooks
        FROM entries e
        LEFT JOIN entry_notebook en ON e.id = en.entry_id
        LEFT JOIN notebooks n ON en.notebook_id = n.id
        WHERE e.title = ?
        GROUP BY e.id
    ''', (title,))
    entry = cursor.fetchone()
    if entry:
        log_operation(conn, 'READ_ENTRY', 'entries', entry[0])
    else:
        log_operation(conn, 'READ_ENTRY_FAILED', 'entries', details=f"Entry '{title}' not found.")
    return entry

def list_notebooks(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT name, state FROM notebooks')
    notebooks = cursor.fetchall()
    log_operation(conn, 'LIST_NOTEBOOKS', 'notebooks')
    return notebooks

def rename_notebook(conn, old_name, new_name):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM notebooks WHERE name = ?', (old_name,))
    notebook_id = cursor.fetchone()
    if notebook_id:
        try:
            cursor.execute('''
                UPDATE notebooks
                SET name = ?
                WHERE id = ?
            ''', (new_name, notebook_id[0]))
            conn.commit()
            log_operation(conn, 'RENAME_NOTEBOOK', 'notebooks', notebook_id[0], f"Notebook '{old_name}' renamed to '{new_name}'.")
            return f"Notebook '{old_name}' renamed to '{new_name}' successfully."
        except sqlite3.IntegrityError:
            log_operation(conn, 'RENAME_NOTEBOOK_FAILED', 'notebooks', notebook_id[0], f"Notebook '{new_name}' already exists.")
            return f"Notebook '{new_name}' already exists."
    else:
        log_operation(conn, 'RENAME_NOTEBOOK_FAILED', 'notebooks', details=f"Notebook '{old_name}' does not exist.")
        return f"Notebook '{old_name}' does not exist."

def list_notes_for_entry(conn, entry_title):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT n.id, n.content, n.timestamp
        FROM notes n
        JOIN entries e ON n.entry_id = e.id
        WHERE e.title = ?
    ''', (entry_title,))
    notes = cursor.fetchall()
    log_operation(conn, 'LIST_NOTES_FOR_ENTRY', 'notes', details=f"Notes for entry '{entry_title}' listed.")
    return notes

def archive_notebook(conn, name):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM notebooks WHERE name = ?', (name,))
    notebook_id = cursor.fetchone()
    if notebook_id:
        cursor.execute('''
            UPDATE notebooks
            SET state = 'archived'
            WHERE id = ?
        ''', (notebook_id[0],))
        conn.commit()
        log_operation(conn, 'ARCHIVE_NOTEBOOK', 'notebooks', notebook_id[0], f"Notebook '{name}' archived.")
        return f"Notebook '{name}' archived successfully."
    else:
        log_operation(conn, 'ARCHIVE_NOTEBOOK_FAILED', 'notebooks', details=f"Notebook '{name}' does not exist.")
        return f"Notebook '{name}' does not exist."

def activate_notebook(conn, name):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM notebooks WHERE name = ?', (name,))
    notebook_id = cursor.fetchone()
    if notebook_id:
        cursor.execute('''
            UPDATE notebooks
            SET state = 'active'
            WHERE id = ?
        ''', (notebook_id[0],))
        conn.commit()
        log_operation(conn, 'ACTIVATE_NOTEBOOK', 'notebooks', notebook_id[0], f"Notebook '{name}' activated.")
        return f"Notebook '{name}' activated successfully."
    else:
        log_operation(conn, 'ACTIVATE_NOTEBOOK_FAILED', 'notebooks', details=f"Notebook '{name}' does not exist.")
        return f"Notebook '{name}' does not exist."

def search_entries(conn, keyword):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.id, e.title, e.content, e.timestamp, e.attachment_path, GROUP_CONCAT(n.name, ', ') as notebooks
        FROM entries e
        LEFT JOIN entry_notebook en ON e.id = en.entry_id
        LEFT JOIN notebooks n ON en.notebook_id = n.id
        WHERE e.title LIKE ? OR e.content LIKE ? OR e.attachment_path LIKE ?
        GROUP BY e.id
    ''', (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    entries = cursor.fetchall()
    log_operation(conn, 'SEARCH_ENTRIES', 'entries', details=f'Search for entries with keyword "{keyword}" returned {len(entries)} result(s).')
    return entries

def search_notes(conn, keyword):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT n.id, n.content, n.timestamp, n.attachment_path, e.title
        FROM notes n
        JOIN entries e ON n.entry_id = e.id
        WHERE n.content LIKE ? OR n.attachment_path LIKE ?
    ''', (f"%{keyword}%", f"%{keyword}%"))
    notes = cursor.fetchall()
    log_operation(conn, 'SEARCH_NOTES', 'notes', details=f'Search for notes with keyword "{keyword}" returned {len(notes)} result(s).')
    return notes

def search_entries_by_tag(conn, tag):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.id, e.title, e.content, e.timestamp, e.attachment_path, GROUP_CONCAT(n.name, ', ') as notebooks
        FROM entries e
        JOIN entry_tags et ON e.id = et.entry_id
        JOIN tags t ON et.tag_id = t.id
        LEFT JOIN entry_notebook en ON e.id = en.entry_id
        LEFT JOIN notebooks n ON en.notebook_id = n.id
        WHERE t.name = ?
        GROUP BY e.id
    ''', (tag,))
    entries = cursor.fetchall()
    log_operation(conn, 'SEARCH_ENTRIES_BY_TAG', 'entries', details=f'Search for entries with tag "{tag}" returned {len(entries)} result(s).')
    return entries

def search_notes_by_tag(conn, tag):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT n.id, n.content, n.timestamp, n.attachment_path, e.title
        FROM notes n
        JOIN note_tags nt ON n.id = nt.note_id
        JOIN tags t ON nt.tag_id = t.id
        JOIN entries e ON n.entry_id = e.id
        WHERE t.name = ?
    ''', (tag,))
    notes = cursor.fetchall()
    log_operation(conn, 'SEARCH_NOTES_BY_TAG', 'notes', details=f'Search for notes with tag "{tag}" returned {len(notes)} result(s).')
    return notes