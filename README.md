# Reposet Tools

A collection of command-line utilities to manage a set of git repositories within a single directory, referred to as a "reposet". These tools help automate cloning, pulling, checking status, and running commands across multiple repositories.

## Scripts

-   `reposet-pull-yaml.py`: Manages the repositories in the directory based on a `repos.yaml` configuration file.
    -   `pull`: Clones new repositories or pulls updates for existing ones.
    -   `check`: Compares the state of the local repositories (remotes, branches) against `repos.yaml`.
    -   `update`: Scans the local directory and generates a `new_repos.yaml` file based on the current state of the git repositories found.

-   `reposet-git.py`: Executes a git command across all repositories in the reposet. It includes a special `state` command to provide a summary of repositories with uncommitted changes or commits that need to be pushed.

-   `reposet-install-develop.py`: Finds and installs Python or Julia projects from the reposet in editable/developer mode using `pip` or `Pkg` respectively.

## Installation

There are a few ways to use these scripts:

1.  **Add to PATH**: Add the directory containing these scripts to your shell's `PATH` environment variable.
    ```bash
    export PATH="/path/to/wield-reposet:$PATH"
    ```
    You may want to add this line to your `.bashrc` or `.zshrc` to make it permanent.

2.  **Symlink**: Create symbolic links to the scripts from a directory that is already in your `PATH` (e.g., `~/.local/bin`).
    ```bash
    ln -s /path/to/wield-reposet/reposet-pull-yaml.py ~/.local/bin/reposet-pull-yaml
    ln -s /path/to/wield-reposet/reposet-git.py ~/.local/bin/reposet-git
    ln -s /path/to/wield-reposet/reposet-install-develop.py ~/.local/bin/reposet-install-develop
    ```

3.  **Self-Managed Repository**: Keep the `wield-reposet` repository itself as one of the repositories in your reposet, and run the scripts using their relative path. This way, the tools themselves are kept up-to-date by `reposet-pull-yaml.py`.

## Usage

### 1. Create a `repos.yaml` file

Create a `repos.yaml` file in the root of your reposet directory. This file defines the repositories you want to manage.

**Example `repos.yaml`:**
```yaml
# The key for each entry is the directory name for the repository.

# This entry manages the tools repository itself.
wield-reposet:
  active: true
  branch: main
  remotes:
    gh: git@github.com:your-username/wield-reposet.git

my-python-project:
  active: true
  branch: main
  remotes:
    origin: git@github.com:your-username/my-python-project.git

another-project:
  active: true
  branch: develop # you can specify a branch other than main/master
  remotes:
    # you can specify multiple remotes
    gitlab: git@gitlab.com:your-username/another-project.git
    github: git@github.com:your-username/another-project.git

old-project:
  # 'active: false' will cause this repository to be skipped
  active: false
  branch: main
  remotes:
    origin: git@github.com:your-username/old-project.git
```

### 2. Manage Repositories with `reposet-pull-yaml.py`

-   **Pull/Clone all active repositories:**
    ```bash
    ./reposet-pull-yaml.py pull
    ```

-   **Check local repositories against `repos.yaml`:**
    ```bash
    ./reposet-pull-yaml.py check
    ```

-   **Generate a new YAML file from existing repositories:**
    ```bash
    ./reposet-pull-yaml.py update
    ```
    This will create a `new_repos.yaml` file.

### 3. Work with Git using `reposet-git.py`

-   **Check the status of all repositories:**
    The `state` command shows which repos have uncommitted changes or commits to push.
    ```bash
    ./reposet-git.py state
    ```

-   **Run any git command across all repositories:**
    ```bash
    # See a short status for all repos
    ./reposet-git.py status -s

    # Fetch all remotes for all repos
    ./reposet-git.py fetch --all
    ```

### 4. Install Projects with `reposet-install-develop.py`

-   **Install all Python and Julia projects in development mode:**
    ```bash
    ./reposet-install-develop.py
    ```
    Any arguments passed to the script will be forwarded to `pip install`.
