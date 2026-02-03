"""
Script to duplicate the current repository into a new separate repository.
This will copy all files (respecting .gitignore) to a new directory and initialize a new git repo there.
"""

import os
import shutil
import subprocess
from pathlib import Path

def read_gitignore():
    """Read .gitignore patterns and convert them to a list of patterns."""
    gitignore_path = Path('../.gitignore')
    if not gitignore_path.exists():
        return []
    
    patterns = []
    with open(gitignore_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(line)
    return patterns

def should_ignore(path, gitignore_patterns):
    """Check if a path should be ignored based on .gitignore patterns."""
    path_str = str(path).replace('\\', '/')
    for pattern in gitignore_patterns:
        # Simple pattern matching (handles basic cases)
        if pattern.startswith('/'):
            pattern = pattern[1:]
        if pattern.endswith('/'):
            pattern = pattern[:-1]
        
        # Check if pattern matches
        if '*' in pattern:
            import fnmatch
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
        else:
            if pattern in path_str or path.name == pattern:
                return True
    return False

def copy_repo_files(source_dir, dest_dir, gitignore_patterns):
    """Copy all files from source to dest, respecting .gitignore."""
    source = Path(source_dir)
    dest = Path(dest_dir)
    
    # Create destination directory
    dest.mkdir(parents=True, exist_ok=True)
    
    copied_files = []
    ignored_files = []
    
    for root, dirs, files in os.walk(source):
        # Skip .git directory if it exists
        if '.git' in dirs:
            dirs.remove('.git')
        
        # Skip __pycache__ and other common ignored dirs
        dirs_to_remove = [d for d in dirs if d in ['.git', '__pycache__', '.pycharm', '.idea', 'venv', '.ipynb_checkpoints', '.data', '_old']]
        for d in dirs_to_remove:
            dirs.remove(d)
        
        rel_root = Path(root).relative_to(source)
        dest_root = dest / rel_root
        
        # Create directory structure
        dest_root.mkdir(parents=True, exist_ok=True)
        
        for file in files:
            source_file = Path(root) / file
            dest_file = dest_root / file
            
            # Check if file should be ignored
            if should_ignore(source_file, gitignore_patterns):
                ignored_files.append(str(source_file))
                continue
            
            # Copy file
            shutil.copy2(source_file, dest_file)
            copied_files.append(str(source_file))
    
    return copied_files, ignored_files

def main():
    import sys
    
    print("Repository Duplication Script")
    print("=" * 50)
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Get destination directory name from command line or use default
    if len(sys.argv) > 1:
        dest_name = sys.argv[1]
    else:
        dest_name = "Data2025_copy"
    
    dest_dir = current_dir.parent / dest_name
    
    if dest_dir.exists():
        print(f"\nWarning: Directory '{dest_dir}' already exists. Removing it...")
        shutil.rmtree(dest_dir)
    
    print(f"\nDestination directory: {dest_dir}")
    
    # Read .gitignore patterns
    print("\nReading .gitignore patterns...")
    gitignore_patterns = read_gitignore()
    print(f"Found {len(gitignore_patterns)} ignore patterns")
    
    # Copy files
    print("\nCopying files...")
    copied_files, ignored_files = copy_repo_files(current_dir, dest_dir, gitignore_patterns)
    print(f"Copied {len(copied_files)} files")
    print(f"Ignored {len(ignored_files)} files")
    
    # Initialize git in destination
    print(f"\nInitializing git repository in {dest_dir}...")
    os.chdir(dest_dir)
    subprocess.run(['git', 'init'], check=True)
    print("Git repository initialized!")
    
    # Copy .gitignore to new repo
    gitignore_source = current_dir / '.gitignore'
    if gitignore_source.exists():
        shutil.copy2(gitignore_source, dest_dir / '.gitignore')
        print("Copied .gitignore")
    
    print("\n" + "=" * 50)
    print("SUCCESS!")
    print(f"New repository created at: {dest_dir}")
    print("\nNext steps:")
    print(f"1. cd {dest_dir}")
    print("2. git add .")
    print("3. git commit -m 'Initial commit'")
    print("4. (Optional) Add a remote: git remote add origin <your-repo-url>")

if __name__ == "__main__":
    main()

