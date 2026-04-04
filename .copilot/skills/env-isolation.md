# Environment Isolation Skill
Always use local virtual environments for dependencies.

## Guidelines
- **ALWAYS** activate the `./.venv` environment with the script inside the project when running `pip` or `python` commands.
- Never install packages to the global Python environment.
- Construct paths to the virtual environment's site-packages and scripts for all terminal operations.
