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

    parser_sync = subparsers.add_parser(
        'sync',
        help='Sync the remotes with the YAML file.'
    )

    args = parser.parse_args()

    if args.command == 'pull':
        pull_repos()
    elif args.command == 'check':
        check_repos()
    elif args.command == 'update':
        update_yaml()
    elif args.command == 'sync':
        sync_repos()

def _setup_repo(repo_name, repo_info):
    # Set up remotes
    remotes = repo_info.get('remotes') or {}

    #remove all existing remotes
    stdout, _ = run_command(f"git remote", cwd=repo_name, capture=True)
    for remote_name in stdout.strip().splitlines():
        if not remote_name:
            continue
        run_command(f"git remote remove {remote_name}", cwd=repo_name, must_succeed=False)

    for remote_name, remote_url in remotes.items():
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

def pull_repos():
    repos = read_yaml_file()

    new_repo_tasks = []
    existing_repo_tasks = []

    for repo_name, repo_info in repos.items():
        if not repo_info.get('active', False):
            continue

        if os.path.isdir(repo_name) and os.path.exists(os.path.join(repo_name, '.git')):
            existing_repo_tasks.append((repo_name, repo_info))
        elif not os.path.exists(repo_name):
            new_repo_tasks.append((repo_name, repo_info))
        else:
            print(f"Skipping {repo_name} as it exists but is not a git repository.")
    # First, pull non-existing directories
    for repo_name, repo_info in new_repo_tasks:
        print(f"Processing {repo_name}...")
        remotes = repo_info.get('remotes') or {}
        if not remotes:
            print(f"No remotes specified for {repo_name}. Skipping clone.")
            continue
        
        first_remote_url = next(iter(remotes.values()))
        run_command(f"git clone {first_remote_url} {repo_name}")
        _setup_repo(repo_name, repo_info)

    # Then, do any updates on existing directories
    for repo_name, repo_info in existing_repo_tasks:
        print(f"Processing {repo_name}...")
        print(f"Repository {repo_name} already exists. Pulling changes.")
        run_command("git pull", cwd=repo_name)
        _setup_repo(repo_name, repo_info)

def sync_repos():
    repos = read_yaml_file()
    for repo_name, repo_info in repos.items():
        if not repo_info.get('active', False):
            continue

        print(f"Syncing {repo_name}...")
        if not os.path.isdir(repo_name) or not os.path.exists(os.path.join(repo_name, '.git')):
            print(f"  - Directory not found or not a git repository.")
            continue
        _setup_repo(repo_name, repo_info)

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

    existing_repos = read_yaml_file()
    
    print("\n--- Differences from existing repos.yaml ---")
    for repo_name, repo_info in new_repos.items():
        if repo_name not in existing_repos:
            print(f"  - New repo: {repo_name}")
            continue
        
        diffs = []
        existing_info = existing_repos[repo_name]
        if repo_info['branch'] != existing_info.get('branch'):
            diffs.append(f"branch: {existing_info.get('branch')} -> {repo_info['branch']}")
        
        if repo_info['remotes'] != existing_info.get('remotes'):
            diffs.append(f"remotes changed")

        if diffs:
            print(f"  - {repo_name}: {', '.join(diffs)}")

    for repo_name in existing_repos:
        if repo_name not in new_repos:
            print(f"  - Repo not found locally: {repo_name}")
    print("----------------------------------------")

    with open(output_filename, 'w') as f:
        yaml.dump(new_repos, f, default_flow_style=False)
    print(f"Updated YAML file written to {output_filename}")

if __name__ == '__main__':
    main()
