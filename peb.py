import os
import argparse
import configparser
import database

# Read configuration file
config = configparser.ConfigParser()
config.read('configuration.ini')

# Database file from configuration
DATABASE_FILE = config.get('database', 'file')
# Attachments directory from configuration
ATTACHMENTS_DIR = config.get('attachments', 'dir')

def initialize_database():
    global DATABASE_FILE, ATTACHMENTS_DIR
    database.DATABASE_FILE = DATABASE_FILE
    database.ATTACHMENTS_DIR = ATTACHMENTS_DIR
    conn = database.get_db_connection()
    database.create_database(conn)
    return conn

def create_notebook(conn, name, api=False):
    message = database.create_notebook(conn, name)
    if api:
        return message
    print(message)

def create_entry(conn, title, content, notebook=None, file_path=None, tags=[], api=False):
    if tags is None:
        tags = []
    notebooks = [notebook] if notebook else []
    messages = database.create_entry(conn, title, content, notebooks, file_path, tags)
    if api:
        return messages
    for message in messages:
        print(message)

def create_note(conn, entry_title, note_content, file_path=None, tags=[], api=False):
    if tags is None:
        tags = []
    message = database.create_note_for_entry(conn, entry_title, note_content, file_path, tags)
    if api:
        return message
    print(message)

def list_entries(conn, api=False):
    entries = database.list_entries(conn)
    if api:
        return entries
    for entry in entries:
        print(f"{entry[0]}: {entry[1]} (Created on {entry[2]}) [Notebooks: {entry[3]}]")

def read_entry(conn, title, api=False):
    entry = database.read_entry_by_title(conn, title)
    if api:
        return entry
    if entry:
        print(f"Title: {entry[0]}\nContent: {entry[1]}\nTimestamp: {entry[2]}\nNotebooks: {entry[3]}")
    else:
        print(f"Entry with title '{title}' does not exist.")

def list_notebooks(conn, api=False):
    notebooks = database.list_notebooks(conn)
    if api:
        return notebooks
    for notebook in notebooks:
        print(f"Name: {notebook[0]}, State: {notebook[1]}")

def rename_notebook(conn, old_name, new_name, api=False):
    message = database.rename_notebook(conn, old_name, new_name)
    if api:
        return message
    print(message)

def list_notes(conn, entry_title, api=False):
    notes = database.list_notes_for_entry(conn, entry_title)
    if api:
        return notes
    for note in notes:
        print(f"Note ID: {note[0]}\nContent: {note[1]}\nTimestamp: {note[2]}")

def archive_notebook(conn, name, api=False):
    message = database.archive_notebook(conn, name)
    if api:
        return message
    print(message)

def activate_notebook(conn, name, api=False):
    message = database.activate_notebook(conn, name)
    if api:
        return message
    print(message)

def search_entries(conn, keyword, api=False):
    entries = database.search_entries(conn, keyword)
    if api:
        return entries
    for entry in entries:
        print(f"{entry[0]}: {entry[1]} (Created on {entry[3]}) [Notebooks: {entry[5]}]")

def search_notes(conn, keyword, api=False):
    notes = database.search_notes(conn, keyword)
    if api:
        return notes
    for note in notes:
        print(f"Note ID: {note[0]}\nContent: {note[1]}\nTimestamp: {note[2]}\nEntry Title: {note[4]}")

def search_entries_by_tag(conn, tag, api=False):
    entries = database.search_entries_by_tag(conn, tag)
    if api:
        return entries
    for entry in entries:
        print(f"{entry[0]}: {entry[1]} (Created on {entry[3]}) [Notebooks: {entry[5]}]")

def search_notes_by_tag(conn, tag, api=False):
    notes = database.search_notes_by_tag(conn, tag)
    if api:
        return notes
    for note in notes:
        print(f"Note ID: {note[0]}\nContent: {note[1]}\nTimestamp: {note[2]}\nEntry Title: {note[4]}")

def main():
    conn = initialize_database()

    parser = argparse.ArgumentParser(description="ProjEB - Command Line Electronic Lab Notebook")
    subparsers = parser.add_subparsers(dest='command')

    # Create notebook command
    create_notebook_parser = subparsers.add_parser('create_notebook', aliases=['cn'], help='Create a new notebook')
    create_notebook_parser.add_argument('--name', type=str, required=True, help='Name of the notebook')

    # Create entry command
    create_parser = subparsers.add_parser('create', aliases=['ce'], help='Create a new entry')
    create_parser.add_argument('--title', type=str, required=True, help='Title of the entry')
    create_parser.add_argument('--content', type=str, required=True, help='Content of the entry')
    create_parser.add_argument('--notebook', type=str, help='Notebook to tag the entry')
    create_parser.add_argument('--file', type=str, help='Path to a file to attach to the entry')
    create_parser.add_argument('--tags', type=str, nargs='*', help='Tags for the entry')

    # Create note command
    create_note_parser = subparsers.add_parser('create_note', aliases=['cnote'], help='Create a new note for an entry')
    create_note_parser.add_argument('--entry_title', type=str, required=True, help='Title of the entry')
    create_note_parser.add_argument('--content', type=str, required=True, help='Content of the note')
    create_note_parser.add_argument('--file', type=str, help='Path to a file to attach to the note')
    create_note_parser.add_argument('--tags', type=str, nargs='*', help='Tags for the note')

    # List entries command
    list_parser = subparsers.add_parser('list', aliases=['ls'], help='List all entries')

    # Read entry command
    read_parser = subparsers.add_parser('read', aliases=['rd'], help='Read an entry')
    read_parser.add_argument('--title', type=str, required=True, help='Title of the entry')

    # List notebooks command
    list_notebooks_parser = subparsers.add_parser('list_notebooks', aliases=['ln'], help='List all notebooks')

    # Rename notebook command
    rename_notebook_parser = subparsers.add_parser('rename_notebook', aliases=['rn'], help='Rename a notebook')
    rename_notebook_parser.add_argument('--old_name', type=str, required=True, help='Current name of the notebook')
    rename_notebook_parser.add_argument('--new_name', type=str, required=True, help='New name of the notebook')

    # Archive notebook command
    archive_notebook_parser = subparsers.add_parser('archive_notebook', aliases=['an'], help='Archive a notebook')
    archive_notebook_parser.add_argument('--name', type=str, required=True, help='Name of the notebook to archive')

    # Activate notebook command
    activate_notebook_parser = subparsers.add_parser('activate_notebook', aliases=['actn'], help='Activate a notebook')
    activate_notebook_parser.add_argument('--name', type=str, required=True, help='Name of the notebook to activate')

    # List notes command
    list_notes_parser = subparsers.add_parser('list_notes', aliases=['lnote'], help='List all notes for an entry')
    list_notes_parser.add_argument('--entry_title', type=str, required=True, help='Title of the entry')

    # Search entries command
    search_entries_parser = subparsers.add_parser('search_entries', aliases=['se'], help='Search for entries based on keywords')
    search_entries_parser.add_argument('--keyword', type=str, required=True, help='Keyword to search for in entries')

    # Search notes command
    search_notes_parser = subparsers.add_parser('search_notes', aliases=['sn'], help='Search for notes based on keywords')
    search_notes_parser.add_argument('--keyword', type=str, required=True, help='Keyword to search for in notes')

    # Search entries by tag command
    search_entries_by_tag_parser = subparsers.add_parser('search_entries_by_tag', aliases=['set'], help='Search for entries by tag')
    search_entries_by_tag_parser.add_argument('--tag', type=str, required=True, help='Tag to search for in entries')

    # Search notes by tag command
    search_notes_by_tag_parser = subparsers.add_parser('search_notes_by_tag', aliases=['snt'], help='Search for notes by tag')
    search_notes_by_tag_parser.add_argument('--tag', type=str, required=True, help='Tag to search for in notes')

    args = parser.parse_args()

    if args.command in ['create_notebook', 'cn']:
        create_notebook(conn, args.name)
    elif args.command in ['create', 'ce']:
        create_entry(conn, args.title, args.content, args.notebook, args.file, args.tags)
    elif args.command in ['create_note', 'cnote']:
        create_note(conn, args.entry_title, args.content, args.file, args.tags)
    elif args.command in ['list', 'ls']:
        list_entries(conn)
    elif args.command in ['read', 'rd']:
        read_entry(conn, args.title)
    elif args.command in ['list_notebooks', 'ln']:
        list_notebooks(conn)
    elif args.command in ['rename_notebook', 'rn']:
        rename_notebook(conn, args.old_name, args.new_name)
    elif args.command in ['archive_notebook', 'an']:
        archive_notebook(conn, args.name)
    elif args.command in ['activate_notebook', 'actn']:
        activate_notebook(conn, args.name)
    elif args.command in ['list_notes', 'lnote']:
        list_notes(conn, args.entry_title)
    elif args.command in ['search_entries', 'se']:
        search_entries(conn, args.keyword)
    elif args.command in ['search_notes', 'sn']:
        search_notes(conn, args.keyword)
    elif args.command in ['search_entries_by_tag', 'set']:
        search_entries_by_tag(conn, args.tag)
    elif args.command in ['search_notes_by_tag', 'snt']:
        search_notes_by_tag(conn, args.tag)
    else:
        parser.print_help()

    conn.close()

if __name__ == "__main__":
    main()