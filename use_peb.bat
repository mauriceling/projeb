@echo off
python peb.py %*

REM Sample commands for ProjEB (Project Electronic Book)
echo Testing ProjEB Commands...
echo.

REM Initialize the system
echo Testing initialization...
python peb.py init
echo.

REM Create a notebook
echo Creating notebooks...
python peb.py create-notebook --name "Lab Work 2025" --description "Laboratory experiments and results for 2025"
python peb.py create-notebook --name "Research Papers" --description "Paper drafts and notes"
echo.

REM List notebooks
echo Listing notebooks...
python peb.py list-notebooks
echo.

REM Create entries
echo Creating entries...
python peb.py create-entry --notebook "Lab Work 2025" --title "Experiment 001" --content "Initial setup test" --tags "setup,test"
python peb.py create-entry --notebook "Lab Work 2025" --title "Experiment 002" --content "Method validation" --tags "validation,method"
echo.

REM Add attachments to entry
echo Adding entry with attachments...
python peb.py create-entry --notebook "Lab Work 2025" --title "Experiment 003" --content "Results analysis" --attachments "sample_data.csv,results.png" --tags "analysis,results"
echo.

REM List entries in a notebook
echo Listing entries in Lab Work 2025...
python peb.py list-entries --notebook "Lab Work 2025"
echo.

REM Create notes for an entry
echo Creating notes...
python peb.py create-note --notebook "Lab Work 2025" --entry "Experiment 001" --content "Updated protocol" --tags "protocol,update"
python peb.py create-note --notebook "Lab Work 2025" --entry "Experiment 001" --content "New observations" --attachments "observation.jpg"
echo.

REM List notes for an entry
echo Listing notes for Experiment 001...
python peb.py list-notes --notebook "Lab Work 2025" --entry "Experiment 001"
echo.

REM Test tag operations
echo Testing tag operations...
python peb.py list-tags
python peb.py rename-tag --old-tag "setup" --new-tag "initialization"
python peb.py merge-tags --tags "test,validation" --new-tag "verification"
echo.

REM Search functionality
echo Testing search...
python peb.py search --query "protocol"
python peb.py search --query "results" --tag "analysis"
echo.

REM Export and backup
echo Testing export and backup...
python peb.py export --format json --output "export_data.json"
python peb.py backup --output "projeb_backup.zip"
echo.

echo ProjEB test commands completed.
pause