#!/usr/bin/env python3
"""
This script provides a way to run a git command against multiple repositories.
It is designed to be run in a directory containing multiple git repositories
as immediate subdirectories.

The script finds all immediate subdirectories, checks if they are git
repositories, and then executes the given git command within each of them.

It also provides a special 'state' command which gives a summary of which
repositories have uncommitted changes (are "dirty"), which have commits
that have not been pushed to their remote upstream branch, and which have no
upstream configured for their current branch.
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
    """Runs a command, captures its output, and returns it as a string.

    Returns stdout stripped of whitespace. Returns None if the command fails or
    is not found. Stderr is suppressed.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def state_command():
    """Checks the git status of each repository in the subfolders.

    It identifies and reports repositories that are "dirty" (have uncommitted
    changes), repositories that have commits that need to be pushed to the
    remote, and repositories whose current branch has no upstream assigned.
    """
    # Get all subdirectories of the current path.
    subfolders = get_subfolders()
    dirty_repos = []
    push_repos = []
    no_upstream_repos = []

    # Iterate over subfolders, checking git status for each.
    for repo in sorted(subfolders):
        # Skip any subdirectories that are not git repositories.
        if not is_git_repo(repo):
            continue

        # Check for dirty state using 'git status --porcelain'.
        # This command provides a concise output of changes. If there is any
        # output, the repository is dirty.
        if run_command_capture(['git', 'status', '--porcelain'], cwd=repo):
            dirty_repos.append(repo)

        # Check for commits to push.
        # First, check if an upstream branch is configured.
        if run_command_capture(['git', 'rev-parse', '@{u}'], cwd=repo) is not None:
            # If so, count commits between upstream and HEAD.
            commits_to_push_str = run_command_capture(['git', 'rev-list', '--count', '@{u}..HEAD'], cwd=repo)
            # If there are commits to push, add to the list.
            if commits_to_push_str and int(commits_to_push_str) > 0:
                push_repos.append(f"{repo} ({commits_to_push_str} commit(s))")
        else:
            # No upstream is configured for the current branch. Report the
            # branch name so it is clear what needs tracking; an empty result
            # means HEAD is detached, which cannot have an upstream at all.
            branch = run_command_capture(['git', 'branch', '--show-current'], cwd=repo)
            if branch:
                no_upstream_repos.append(f"{repo} (branch '{branch}')")
            else:
                no_upstream_repos.append(f"{repo} (detached HEAD)")

    # Report the findings.
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

    if no_upstream_repos:
        print("\nRepositories with no upstream for the current branch:")
        for repo in no_upstream_repos:
            print(f"  - {repo}")
    else:
        print("\nAll repositories have an upstream for the current branch.")

def main():
    """Main function to parse arguments and execute commands."""
    # The script requires at least one argument (the git command or 'state').
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <git command> | state")
        sys.exit(1)

    # Handle the special 'state' command.
    if sys.argv[1] == 'state':
        state_command()
        return

    # For any other command, prepend 'git' and prepare for execution.
    git_cmd = ['git'] + sys.argv[1:]
    subfolders = get_subfolders()
    
    error_occurred = False
    # Iterate through subfolders and run the git command in each git repository.
    for repo in sorted(subfolders):
        if is_git_repo(repo):
            print(f"\n--- Executing in {repo} ---")
            try:
                # Run the command. Output is passed through to the user's terminal.
                # Passthrough stdout/stderr
                subprocess.run(git_cmd, cwd=repo, check=True)
            except subprocess.CalledProcessError:
                # If a command fails in one repo, note it and continue.
                error_occurred = True
            except FileNotFoundError:
                # This handles the case where 'git' is not installed or not in PATH.
                print("Error: 'git' command not found.", file=sys.stderr)
                sys.exit(1)
    
    # Exit with a non-zero status code if any command failed.
    if error_occurred:
        sys.exit(1)

if __name__ == "__main__":
    main()
