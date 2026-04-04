# Windows PowerShell build script for PyInstaller Gradio app
# Cleans up old build artifacts and runs PyInstaller with --clean

# Remove old build and dist folders if they exist
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path __pycache__) { Remove-Item -Recurse -Force __pycache__ }

# Run PyInstaller with --clean
pyinstaller --clean workflow_gui_gradio.spec

Write-Host "Build complete. Check the dist/ folder for your executable."
