import os
import argparse
import configparser
import database

# Read configuration file
config = configparser.ConfigParser()
config.read('configuration.ini')

# Database file from configuration
DATABASE_FILE = config.get('database', 'file')

def initialize_database():
    global DATABASE_FILE
    database.DATABASE_FILE = DATABASE_FILE
    conn = database.get_db_connection()
    database.create_database(conn)
    return conn

def create_notebook_command(conn, name, api=False):
    message = database.create_notebook(conn, name)
    if api:
        return message
    print(message)

def create_entry_command(conn, title, content, notebook=None, api=False):
    notebooks = [notebook] if notebook else []
    messages = database.create_entry(conn, title, content, notebooks)
    if api:
        return messages
    for message in messages:
        print(message)

def list_entries_command(conn, api=False):
    entries = database.list_entries(conn)
    if api:
        return entries
    for entry in entries:
        print(f"{entry[0]}: {entry[1]} (Created on {entry[2]}) [Notebooks: {entry[3]}]")

def read_entry_command(conn, title, api=False):
    entry = database.read_entry_by_title(conn, title)
    if api:
        return entry
    if entry:
        print(f"Title: {entry[0]}\nContent: {entry[1]}\nTimestamp: {entry[2]}\nNotebooks: {entry[3]}")
    else:
        print(f"Entry with title '{title}' does not exist.")

def main():
    conn = initialize_database()

    parser = argparse.ArgumentParser(description="ProjEB - Command Line Electronic Lab Notebook")
    subparsers = parser.add_subparsers(dest='command')

    # Create notebook command
    create_notebook_parser = subparsers.add_parser('create_notebook', help='Create a new notebook')
    create_notebook_parser.add_argument('--name', type=str, required=True, help='Name of the notebook')

    # Create entry command
    create_parser = subparsers.add_parser('create', help='Create a new entry')
    create_parser.add_argument('--title', type=str, required=True, help='Title of the entry')
    create_parser.add_argument('--content', type=str, required=True, help='Content of the entry')
    create_parser.add_argument('--notebook', type=str, help='Notebook to tag the entry')

    # List entries command
    list_parser = subparsers.add_parser('list', help='List all entries')

    # Read entry command
    read_parser = subparsers.add_parser('read', help='Read an entry')
    read_parser.add_argument('--title', type=str, required=True, help='Title of the entry')

    args = parser.parse_args()

    if args.command == 'create_notebook':
        create_notebook_command(conn, args.name)
    elif args.command == 'create':
        create_entry_command(conn, args.title, args.content, args.notebook)
    elif args.command == 'list':
        list_entries_command(conn)
    elif args.command == 'read':
        read_entry_command(conn, args.title)
    else:
        parser.print_help()

    conn.close()

if __name__ == "__main__":
    main()