#!/usr/bin/env python3
"""
This script loops through immediate subdirectories and installs them in
development mode.

It checks if a subdirectory is a Python or Julia project and uses the
appropriate package manager (pip or Julia's Pkg) to install it.

For Python projects (containing setup.py or pyproject.toml), it runs
`pip install -e <path>`. Any arguments passed to this script are forwarded to pip.

For Julia projects (containing Project.toml), it adds the package to the
default Julia environment in development mode.
"""

import os
import subprocess
import sys

def get_subfolders():
    """Returns a list of immediate subdirectories."""
    return [d for d in os.listdir('.') if os.path.isdir(d)]

def is_python_project(path):
    """Checks if a given path appears to be a Python project."""
    return os.path.exists(os.path.join(path, 'setup.py')) or \
           os.path.exists(os.path.join(path, 'pyproject.toml'))

def is_julia_project(path):
    """Checks if a given path appears to be a Julia project."""
    return os.path.exists(os.path.join(path, 'Project.toml'))

def main():
    """Main function to find and install projects."""
    subfolders = get_subfolders()
    pip_args = sys.argv[1:]
    
    error_occurred = False
    for repo in sorted(subfolders):
        if is_python_project(repo):
            print(f"\n--- Installing Python project: {repo} ---")
            try:
                cmd = ['pip', 'install'] + pip_args + ['-e', f'./{repo}']
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                print(f"Error installing Python project in {repo}", file=sys.stderr)
                error_occurred = True
            except FileNotFoundError:
                print("Error: 'pip' command not found.", file=sys.stderr)
                sys.exit(1)
        elif is_julia_project(repo):
            print(f"\n--- Installing Julia project: {repo} ---")
            try:
                repo_abs_path = os.path.abspath(repo)
                julia_code = f'using Pkg; Pkg.develop(path="{repo_abs_path}")'
                cmd = ['julia', '-e', julia_code]
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                print(f"Error installing Julia project in {repo}", file=sys.stderr)
                error_occurred = True
            except FileNotFoundError:
                print("Error: 'julia' command not found.", file=sys.stderr)
                sys.exit(1)

    if error_occurred:
        sys.exit(1)

if __name__ == "__main__":
    main()
