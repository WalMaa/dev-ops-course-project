import json
import os
import logging
from pydriller import Repository

from util import LogLevel, log_and_print

def pydrill(repository_path, filtered_commits, logger):
    data = []
    repo_name = os.path.basename(repository_path.strip('/'))
    
    for commit in Repository(repository_path, only_commits=filtered_commits).traverse_commits():
        commit_data = {
            "commit_hash": commit.hash,
            "previous_commit_hash": commit.parents[0] if commit.parents else None,
            "diff stats": [],
            "diff content": [],
        }
        for m in commit.modified_files:
            diff_stats = {
                "modified": m.filename,
                "added_lines": m.added_lines,
                "deleted_lines": m.deleted_lines,
            }
            diff_content = {
                "modified": m.filename,
                "diff": m.diff_parsed,
            }
            
            commit_data["diff stats"].append(diff_stats)
            commit_data["diff content"].append(diff_content)

        data.append(commit_data)
    
    log_and_print(logger, LogLevel.INFO, f"Pydriller finished: {repo_name}")
    result = f"results/pydriller_results/{repo_name}.json" 

    with open(result, "w") as f:
        json.dump(data, f, indent=4)

def get_refactored_commits(repository, logger):
    repository_path = f"results/miner_results/{repository}.json"
    
    try:
        with open(repository_path, 'r') as file:
            minerJSON = json.load(file)
        
        filtered_commits = [
            commit["sha1"] for commit in minerJSON["commits"] if commit.get("refactorings")
        ]
        return ("OK!", filtered_commits)

    except json.JSONDecodeError:
        log_and_print(logger, LogLevel.WARNING, f"Warning! Could not decode {repository}.json")
        return ["Warning!", "Could not decode JSON file"]
    
    except FileNotFoundError:
        log_and_print(logger, LogLevel.WARNING, f"Warning! Could not find {repository}.json")
        return ["Warning!", "Could not find JSON file"]
    
    except Exception as e:
        log_and_print(logger, LogLevel.ERROR, f"Unexpected error occurred: {e}")
        return ["Error!", f"Unexpected error occurred: {e}"]
    
def run_pydriller(cloned_repositories_dir):
    
    logger = logging.getLogger("pydriller_logger")
        
    count = 0
    succesful_repos = []
    skipped_repos = []
    error_repos = []
    
    os.makedirs("results", exist_ok=True)
    os.makedirs("results/pydriller_results", exist_ok=True)
    
    repository_directories = [
        f.path for f in os.scandir(cloned_repositories_dir) if f.is_dir()
    ]
    
    if len(repository_directories) == 0:
        log_and_print(logger, LogLevel.WARNING, f"No cloned repositories found in {cloned_repositories_dir}")
        return
    
    log_and_print(logger, LogLevel.INFO, f"\nTotal count of repositories: {len(repository_directories)}")
    
    for repo_path in repository_directories:
        count += 1
        repo_name = os.path.basename(repo_path.strip('/'))
        log_and_print(logger, LogLevel.INFO, f"\nChecking repository: {repo_name} ({count}/{len(repository_directories)})")
        
        status, filtered_commits = get_refactored_commits(repo_name, logger)
        
        if  status in ["Warning!", "Error!"] and filtered_commits:
            error_repos.append((repo_name, filtered_commits))
            continue
        if  status in ["OK!"] and filtered_commits:
            log_and_print(logger, LogLevel.INFO, f"Total count of refactored commits: {len(filtered_commits)}")
            log_and_print(logger, LogLevel.INFO, f"Pydriller started: {repo_name}")
            pydrill(repo_path, filtered_commits, logger)
            succesful_repos.append(repo_name)
        else:
            log_and_print(logger, LogLevel.INFO, f"No refactoring detected in {repo_name}, skipping repository.")
            skipped_repos.append(repo_name)
    
    if succesful_repos:
        succesful_repos.sort()
        log_and_print(logger, LogLevel.INFO, f"\nSuccessfully pydrilled {len(succesful_repos)}/{len(repository_directories)} repositories:")
        for repo in succesful_repos:
            log_and_print(logger, LogLevel.INFO, f"-{repo}")

    if skipped_repos:
        skipped_repos.sort()
        log_and_print(logger, LogLevel.INFO, f"\nSkipped {len(skipped_repos)}/{len(repository_directories)} repositories due to no refactoring detected or failure:")
        for repo in skipped_repos:
            log_and_print(logger, LogLevel.INFO, f"-{repo}")
    
    if error_repos:
        error_repos.sort()
        log_and_print(logger, LogLevel.ERROR, f"\nFailed to pydrill {len(error_repos)}/{len(repository_directories)} repositories:")
        for repo, reason in error_repos:
            log_and_print(logger, LogLevel.ERROR, f"-{repo}: {reason}")
