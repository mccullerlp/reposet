#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml
import os
import sys
import argparse
import subprocess
from collections import defaultdict

def run_command(cmd, cwd='.', must_succeed=True, capture=False):
    """
    Runs a command in a subprocess.
    """
    print(f"+ {cmd}")

    stdout_val = subprocess.PIPE if capture else None
    stderr_val = subprocess.PIPE if capture else None

    proc = subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=stdout_val,
        stderr=stderr_val,
    )

    if must_succeed and proc.returncode != 0:
        print(f"Command failed: {cmd}")
        if capture:
            print(proc.stdout.decode('utf-8'))
            print(proc.stderr.decode('utf-8'))
        sys.exit(1)

    if capture:
        return proc.stdout.decode('utf-8'), proc.stderr.decode('utf-8')
    else:
        return None, None

def read_yaml_file(filepath='repos.yaml'):
    """
    Reads the YAML file.
    """
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(
        description=(
            'Pull and manage git repositories based on a YAML file.'
        )
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_pull = subparsers.add_parser(
        'pull',
        help='Pull repositories from the YAML file.'
    )

    parser_check = subparsers.add_parser(
        'check',
        help='Check if the current repositories are consistent with the YAML file.'
    )

    parser_update = subparsers.add_parser(
        'update',
        help='Update the YAML file based on the current repositories.'
    )

    args = parser.parse_args()

    if args.command == 'pull':
        pull_repos()
    elif args.command == 'check':
        check_repos()
    elif args.command == 'update':
        update_yaml()

def pull_repos():
    repos = read_yaml_file()
    for repo_name, repo_info in repos.items():
        if not repo_info.get('active', False):
            continue

        print(f"Processing {repo_name}...")
        if not os.path.exists(repo_name):
            # Clone the repo if it doesn't exist
            remotes = repo_info.get('remotes', {})
            if not remotes:
                print(f"No remotes specified for {repo_name}. Skipping.")
                continue
            
            first_remote_url = next(iter(remotes.values()))
            run_command(f"git clone {first_remote_url} {repo_name}")
        else:
            print(f"Repository {repo_name} already exists. Pulling changes.")
            run_command("git pull", cwd=repo_name)


        # Set up remotes
        remotes = repo_info.get('remotes', {})
        for remote_name, remote_url in remotes.items():
            # first remove the remote in case it has changed
            run_command(f"git remote remove {remote_name}", cwd=repo_name, must_succeed=False)
            run_command(f"git remote add {remote_name} {remote_url}", cwd=repo_name)

        # Fetch all remotes
        run_command("git fetch --all", cwd=repo_name)

        # Check out the specified branch
        branch = repo_info.get('branch', 'main')
        run_command(f"git checkout {branch}", cwd=repo_name)

        # Set the upstream for the branch to the first remote
        if remotes:
            first_remote_name = next(iter(remotes.keys()))
            run_command(f"git branch --set-upstream-to={first_remote_name}/{branch}", cwd=repo_name, must_succeed=False)

def check_repos():
    repos = read_yaml_file()
    for repo_name, repo_info in repos.items():
        if not repo_info.get('active', False):
            continue

        print(f"Checking {repo_name}...")
        if not os.path.exists(repo_name):
            print(f"  - Directory not found.")
            continue

        # Check remotes
        remotes = repo_info.get('remotes', {})
        stdout, _ = run_command(f"git remote -v", cwd=repo_name, capture=True)
        current_remotes = {}
        for line in stdout.strip().splitlines():
            if not line:
                continue
            name, url, _ = line.split()
            current_remotes[name] = url
        
        for remote_name, remote_url in remotes.items():
            if current_remotes.get(remote_name) != remote_url:
                print(f"  - Remote '{remote_name}' mismatch. Expected {remote_url}, found {current_remotes.get(remote_name)}")

        # Check branch
        branch = repo_info.get('branch', 'main')
        stdout, _ = run_command("git rev-parse --abbrev-ref HEAD", cwd=repo_name, capture=True)
        current_branch = stdout.strip()
        if current_branch != branch:
            print(f"  - Branch mismatch. Expected {branch}, found {current_branch}")

def update_yaml(output_filename='new_repos.yaml'):
    new_repos = {}
    for item in os.listdir('.'):
        if os.path.isdir(item) and os.path.exists(os.path.join(item, '.git')):
            print(f"Scanning {item}...")
            repo_name = item
            
            # Get branch
            stdout, _ = run_command("git rev-parse --abbrev-ref HEAD", cwd=repo_name, capture=True)
            branch = stdout.strip()

            # Get remotes
            stdout, _ = run_command("git remote -v", cwd=repo_name, capture=True)
            remotes = {}
            for line in stdout.strip().splitlines():
                if not line:
                    continue
                name, url, fetch_or_push = line.split()
                if '(fetch)' in fetch_or_push:
                    remotes[name] = url

            new_repos[repo_name] = {
                'active': True,
                'branch': branch,
                'remotes': remotes,
            }
    
    with open(output_filename, 'w') as f:
        yaml.dump(new_repos, f, default_flow_style=False)
    print(f"Updated YAML file written to {output_filename}")

if __name__ == '__main__':
    main()
