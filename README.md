# Project Entries Binder: A Command-Line Interface (CLI)-based Electronic Notebook / Binder

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/mauriceling/projeb/)](https://archive.softwareheritage.org/browse/origin/directory/?origin_url=https://github.com/mauriceling/projeb/)

## Overview

Project Entries Binder (ProjEB) is a Command-Line Interface (CLI)-based Electronic Notebook / Binder designed to help you manage project entries, notebooks, and notes efficiently. It is built with Python and offers a variety of features to organize and search your project-related information.

## Features

### 1. Initialization

- **Initialize Database**: Set up the database and attachments directory based on the configuration file (`configuration.ini`).

### 2. Notebook Management

- **Create Notebook**: Create a new notebook to organize your entries.
- **List Notebooks**: List all existing notebooks with their names and states.
- **Rename Notebook**: Rename an existing notebook.
- **Archive Notebook**: Archive a notebook to hide it from the active list.
- **Activate Notebook**: Reactivate an archived notebook.

### 3. Entry Management

- **Create Entry**: Create a new entry with a title, content, and optional notebook, file attachment, and tags.
- **List Entries**: List all entries with their titles, creation dates, and associated notebooks.
- **Read Entry**: Read the content of an entry by its title.
- **Search Entries**: Search for entries based on keywords.
- **Search Entries by Tag**: Search for entries based on tags.

### 4. Note Management

- **Create Note**: Create a new note for an existing entry with optional file attachment and tags.
- **List Notes**: List all notes for a specific entry.
- **Search Notes**: Search for notes based on keywords.
- **Search Notes by Tag**: Search for notes based on tags.

## Usage

### Command-Line Interface

ProjEB provides a comprehensive CLI for managing your notebooks, entries, and notes. Here are some examples of how to use the CLI:

- **Create a Notebook**:
  ```bash
  python peb.py create_notebook --name "My Notebook"
  ```

- **Create an Entry**:
  ```bash
  python peb.py create --title "My Entry" --content "This is the content of my entry." --notebook "My Notebook" --file "path/to/file" --tags "tag1" "tag2"
  ```

- **Create a Note**:
  ```bash
  python peb.py create_note --entry_title "My Entry" --content "This is a note for my entry." --file "path/to/file" --tags "noteTag1" "noteTag2"
  ```

- **List Entries**:
  ```bash
  python peb.py list
  ```

- **Read an Entry**:
  ```bash
  python peb.py read --title "My Entry"
  ```

- **Search Entries**:
  ```bash
  python peb.py search_entries --keyword "search term"
  ```

## Configuration

Ensure you have a `configuration.ini` file with the following structure:

```ini
[database]
file = your_database_file.db

[attachments]
dir = your_attachments_directory
```

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please create an issue or pull request with your suggestions or improvements.

## Contact

For questions or support, please contact [mauriceling](https://github.com/mauriceling).
