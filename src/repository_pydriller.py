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

def get_refactored_commits(repository):
    repository_path = f"results/miner_results/{repository}.json"
    
    try:
        with open(repository_path, 'r') as file:
            minerJSON = json.load(file)
        
        filtered_commits = [
            commit["sha1"] for commit in minerJSON["commits"] if commit.get("refactorings")
        ]
        return filtered_commits

    except json.JSONDecodeError:
        print(f"Warning! Could not decode {repository}")
        return []
    
    except FileNotFoundError:
        print(f"Warning! Could not find {repository}")
        return []
    
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return []
    
def run_pydriller(cloned_repositories_dir):
    
    count = 0

    succesful_repos = []
    skipped_repos = []
    
    os.makedirs("results", exist_ok=True)
    os.makedirs("results/pydriller_results", exist_ok=True)
    
    repository_directories = [
        f.path for f in os.scandir(cloned_repositories_dir) if f.is_dir()
    ]
    
    if len(repository_directories) == 0:
        print(f"No cloned repositories found in {cloned_repositories_dir}")
        return
    
    print(f"\nTotal count of repositories: {len(repository_directories)}")
    
    for repo_path in repository_directories:
        count += 1
        repo_name = os.path.basename(repo_path.strip('/'))
        print(f"\nChecking repository: {repo_name}. ({count}/{len(repository_directories)})")
        
        filtered_commits = get_refactored_commits(repo_name)
        
        if filtered_commits:
            print(f"Total count of refactored commits: {len(filtered_commits)}")
            print(f"Pydriller started: {repo_name}")
            pydrill(repo_path)
            succesful_repos.append(repo_name)
        else:
            print(f"No refactoring detected in {repo_name}, skipping repository.")
            skipped_repos.append(repo_name)
    
    if succesful_repos:
        succesful_repos.sort()
        print(f"\nSuccessfully pydrilled {len(succesful_repos)}/{len(repository_directories)} repositories:")
        for repo in succesful_repos:
            print(f"-{repo}")

    if skipped_repos:
        skipped_repos.sort()
        print(f"\nSkipped {len(skipped_repos)}/{len(repository_directories)} repositories due to no refactoring detected or failure:")
        for repo in skipped_repos:
            print(f"-{repo}")