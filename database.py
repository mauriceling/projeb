import sqlite3
from datetime import datetime

# Database file from configuration
DATABASE_FILE = None

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
            timestamp TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notebooks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
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
    conn.commit()

def create_notebook(conn, name):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO notebooks (name)
            VALUES (?)
        ''', (name,))
        conn.commit()
        return f"Notebook '{name}' created successfully."
    except sqlite3.IntegrityError:
        return f"Notebook '{name}' already exists."

def create_entry(conn, title, content, notebooks):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO entries (title, content, timestamp)
        VALUES (?, ?, ?)
    ''', (title, content, timestamp))
    entry_id = cursor.lastrowid
    
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
            else:
                messages.append(f"Notebook '{notebook}' does not exist. Entry not tagged to this notebook.")
    
    conn.commit()
    messages.append(f"Entry '{title}' created successfully.")
    return messages

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
    return entry