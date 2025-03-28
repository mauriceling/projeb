#!/bin/sh

# Usage examples for ProjEB CLI (peb.py)

# Create a new notebook
python peb.py create_notebook --name "Experiment Notebook"

# Create a new entry tagged to a notebook
python peb.py create --title "Experiment Title" --content "Content of the experiment." --notebook "Experiment Notebook"

# Create a new entry without tagging to a notebook
python peb.py create --title "Experiment Title 2" --content "Content of the second experiment."

# List all entries
python peb.py list

# Read a specific entry by title
python peb.py read --title "Experiment Title"