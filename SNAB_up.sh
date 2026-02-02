#!/bin/bash
# Wrapper to run SNAB_up.ps1 from Git Bash
SCRIPT_DIR=$(dirname "$0")
# Convert path to Windows format for PowerShell if needed, but relative path usually works
powershell.exe -ExecutionPolicy Bypass -File "$SCRIPT_DIR/SNAB_up.ps1" "$@"
