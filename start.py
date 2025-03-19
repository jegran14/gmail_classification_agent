#!/usr/bin/env python3
import os
import subprocess
import sys
import venv

VENV_DIR = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
APP_FILE = "fronted/app.py"

print("Starting Gmail Agent setup...")

# Check if virtual environment exists, create if it doesn't
if not os.path.exists(VENV_DIR):
    print("Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True)
else:
    print("Virtual environment found.")

# Determine path to python and pip in the virtual environment
if sys.platform == 'win32':
    python_exe = os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    pip_exe = os.path.join(VENV_DIR, 'Scripts', 'pip.exe')
else:
    python_exe = os.path.join(VENV_DIR, 'bin', 'python')
    pip_exe = os.path.join(VENV_DIR, 'bin', 'pip')

# Install/upgrade dependencies
print(f"Installing dependencies from {REQUIREMENTS_FILE}...")
subprocess.check_call([pip_exe, 'install', '-U', '-r', REQUIREMENTS_FILE])

# Check if app.py exists
if not os.path.exists(APP_FILE):
    print(f"Error: {APP_FILE} not found.")
    print("Please create an app.py file before running this script.")
    sys.exit(1)

# Run the application
print("Starting application...")
subprocess.check_call([python_exe, APP_FILE])

print("Application stopped.")
