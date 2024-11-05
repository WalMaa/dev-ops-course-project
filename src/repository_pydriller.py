import json
import os
from pydriller import Repository

def pydrill(repository_path):
    data = []

    for commit in Repository(repository_path).traverse_commits():
        commit_data = {
            "commit_hash": commit.hash,
            "previous_commit_hash": commit.parents[0] if commit.parents else None,
            "added lines": commit.insertions,
            "deleted lines": commit.deletions,
            "modified_files": [],
        }
        for m in commit.modified_files:
            file_change_data = {
                "modified": m.filename,
                "added_lines": m.added_lines,
                "deleted_lines": m.deleted_lines,
            }
            commit_data["modified_files"].append(file_change_data)

        data.append(commit_data)
    
    repo_name = os.path.basename(repository_path.strip('/'))
    print(f"Pydriller finished: {repo_name}")
    result = f"results/pydriller_results/{repo_name}.json" 

    with open(result, "w") as f:
        json.dump(data, f, indent=4)

def run_pydriller(cloned_repositories_dir):
    
    count = 0
    
    os.makedirs("results", exist_ok=True)
    os.makedirs("results/pydriller_results", exist_ok=True)
    
    repository_directories = [
        f.path for f in os.scandir(cloned_repositories_dir) if f.is_dir()
    ]
    
    repository_count = len(repository_directories)
    
    print(f"Total count of repositories: {repository_count}")
    
    for repo_path in repository_directories:
        count +=1
        repo_name = os.path.basename(repo_path.strip('/'))
        print(f"Pydriller started: {repo_name} ({count}/{repository_count})")       
        pydrill(repo_path)