@echo off
echo Setting up your game environment...
python -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
echo Environment setup complete!
pause
