@echo off

REM Usage examples for ProjEB CLI (peb.py)

REM Create a new notebook
python peb.py create_notebook --name "Experiment Notebook"

REM Create a new entry tagged to a notebook
python peb.py create --title "Experiment Title" --content "Content of the experiment." --notebook "Experiment Notebook"

REM Create a new entry without tagging to a notebook
python peb.py create --title "Experiment Title 2" --content "Content of the second experiment."

REM Create a new entry with a file attachment
python peb.py create --title "Experiment Title with File" --content "Content of the experiment with file." --notebook "Experiment Notebook" --file "peb.py"

REM Create a new note for an entry
python peb.py create_note --entry_title "Experiment Title" --content "This is a note for the experiment."

REM Create a new note for an entry with a file attachment
python peb.py create_note --entry_title "Experiment Title" --content "This is a note with file for the experiment." --file "peb.py"

REM Create a new entry with tags
python peb.py create --title "Tagged Entry" --content "Content of the tagged entry." --notebook "Experiment Notebook" --tags tag1 tag2

REM Create a new note with tags for an entry
python peb.py create_note --entry_title "Experiment Title" --content "This is a note with tags." --tags tag1 tag2

REM Search for entries based on keywords in titles, content, or attached files
python peb.py search_entries --keyword "experiment"

REM Search for notes based on keywords in content or attached files
python peb.py search_notes --keyword "note"

REM Search for entries by tag
python peb.py search_entries_by_tag --tag "tag1"

REM Search for notes by tag
python peb.py search_notes_by_tag --tag "tag2"

REM Archive a notebook
python peb.py archive_notebook --name "Experiment Notebook"

REM Activate a notebook
python peb.py activate_notebook --name "Experiment Notebook"

REM List all notebooks
python peb.py list_notebooks

REM Rename a notebook
python peb.py rename_notebook --old_name "Experiment Notebook" --new_name "Experiment Renamed Notebook"

REM List all notes for an entry
python peb.py list_notes --entry_title "Experiment Title"
