@echo off

REM Activate the virtual environment
call scripts\activate.bat

REM Run your script
python main_gui.py

REM Optional: Pause to see output if running from double-click
pause
