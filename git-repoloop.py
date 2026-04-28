#!/usr/bin/env python3
"""
Run a git command in each immediate subfolder that is a git repository.
A special 'state' command is available to check for dirty repos or repos with
commits to push.
"""

import os
import subprocess
import sys

def get_subfolders():
    """Returns a list of immediate subdirectories."""
    return [d for d in os.listdir('.') if os.path.isdir(d)]

def is_git_repo(path):
    """Checks if a given path is a git repository."""
    return os.path.isdir(os.path.join(path, '.git'))

def run_command_capture(cmd, cwd='.'):
    """Runs a command and captures its output. Returns stdout or None on error."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            stderr=subprocess.DEVNULL
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def state_command():
    """Checks the state of git repositories in subfolders."""
    subfolders = get_subfolders()
    dirty_repos = []
    push_repos = []

    for repo in sorted(subfolders):
        if not is_git_repo(repo):
            continue

        # Check for dirty state
        if run_command_capture(['git', 'status', '--porcelain'], cwd=repo):
            dirty_repos.append(repo)

        # Check for commits to push
        if run_command_capture(['git', 'rev-parse', '@{u}'], cwd=repo) is not None:
            commits_to_push_str = run_command_capture(['git', 'rev-list', '--count', '@{u}..HEAD'], cwd=repo)
            if commits_to_push_str and int(commits_to_push_str) > 0:
                push_repos.append(f"{repo} ({commits_to_push_str} commit(s))")

    if dirty_repos:
        print("Repositories with uncommitted changes:")
        for repo in dirty_repos:
            print(f"  - {repo}")
    else:
        print("No repositories with uncommitted changes.")

    if push_repos:
        print("\nRepositories with commits to push:")
        for repo in push_repos:
            print(f"  - {repo}")
    else:
        print("\nNo repositories with commits to push.")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <git command> | state")
        sys.exit(1)

    if sys.argv[1] == 'state':
        state_command()
        return

    git_cmd = ['git'] + sys.argv[1:]
    subfolders = get_subfolders()
    
    error_occurred = False
    for repo in sorted(subfolders):
        if is_git_repo(repo):
            print(f"\n--- Executing in {repo} ---")
            try:
                # Passthrough stdout/stderr
                subprocess.run(git_cmd, cwd=repo, check=True)
            except subprocess.CalledProcessError:
                error_occurred = True
            except FileNotFoundError:
                print("Error: 'git' command not found.", file=sys.stderr)
                sys.exit(1)
    
    if error_occurred:
        sys.exit(1)

if __name__ == "__main__":
    main()
