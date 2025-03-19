#!/bin/bash

VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
APP_FILE="app.py"

echo "Starting Gmail Agent setup..."

# Check if virtual environment exists, create if it doesn't
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "Virtual environment found."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies from $REQUIREMENTS_FILE..."
pip install -U -r $REQUIREMENTS_FILE

# Check if app.py exists
if [ ! -f "$APP_FILE" ]; then
    echo "Error: $APP_FILE not found."
    echo "Please create an app.py file before running this script."
    exit 1
fi

# Run the application
echo "Starting application..."
python $APP_FILE

# Deactivate virtual environment on exit
deactivate
echo "Application stopped. Virtual environment deactivated."
