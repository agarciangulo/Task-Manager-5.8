#!/bin/bash

# Clean up Python project before pushing to GitHub

echo "Cleaning up project for GitHub..."

# Remove virtual environments and sensitive files
echo "Removing virtual environments and sensitive files..."
rm -rf venv env .env *.db *.sqlite *.log

# Remove Python cache files
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Reminder for .env.example
echo ""
echo "[Reminder] Make sure you have a .env.example file with placeholder values for others to use."
echo "[Reminder] Do NOT commit your real .env file or venv directory."

echo ""
echo "Cleanup complete! Safe to add, commit, and push to GitHub." 