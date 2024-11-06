import subprocess
import os
import json
import configparser

"""
This module is responsible for calculating the touched lines of code for each refactoring and each developer effort. Task E in the project handout
"""
config = configparser.ConfigParser()
config.read("config.ini")
cloned_repositories_dir = config["paths"]["cloned_repositories_dir"]
dest_dir = "results/tloc_results"

async def calculate(refactoring_results_dir: str):
    print("developer effort calculation")
    os.makedirs(dest_dir, exist_ok=True)
    
    files = [
        (f.path, f.name)
        for f in os.scandir(refactoring_results_dir)
        if f.is_file() and f.name.endswith(".json")
    ]
    
    if len(files) < 1:
        print("Refactoring results not found")
        return
    for index,file in enumerate(files):
        print(f"Processing file {index + 1} of {len(files)}")
        await process_file(file[0], file[1])
        
    
    
async def process_file(file_path : str, file_name : str):
    
    repository_name = file_name.replace(".json", "")
    
    print(f"Processing file: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        refactoring_results = json.load(file)
        
    commits = refactoring_results["commits"]
    commit_results = []
    for index, commit in enumerate(commits):
        if len(commit["refactorings"]) == 0:
            continue
        if index + 1 < len(commits):
            try:
                tlocs = calculate_tlocs(repository_name, commit["sha1"], commits[index + 1]["sha1"]) 
                commit_results.append({"commit": commit["sha1"], "tlocs": tlocs})
            except ValueError as e:
                print(f"Error calculating TLOCs for commit {commit['sha1']} in repository {repository_name}: {e}")
            
    if len(commit_results) == 0:
        print(f"Was unable to calculate refactorings for: {repository_name}")
    else:
        with open(f"{dest_dir}/{repository_name}.json", "w", encoding="utf-8") as file:
            json.dump({"repository": repository_name,
                        "refactorings": commit_results}, file)

    
def get_loc(repository_name: str, commit_sha: str):
    repo_dir = os.path.join(cloned_repositories_dir, repository_name)
    lock_file = os.path.join(repo_dir, ".git", "index.lock")
    
    if os.path.exists(lock_file):
        os.remove(lock_file)
    
    try:
        subprocess.run(["git", "checkout", "-f", commit_sha], check=True, cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result = subprocess.run(["scc", "--no-cocomo", "--no-complexity", "--no-size"], encoding="utf-8",  capture_output=True, text=True, cwd=repo_dir)
        # Parse the output to get the total lines of code
        loc = 0
        for line in result.stdout.splitlines():
            parts = line.split()
            if (len(parts) > 1 and parts[0] == "Total"):
                loc = int(parts[2])
                    
        return loc
    
    except subprocess.CalledProcessError as e:
        print(f"Error checking out commit {commit_sha} in repository {repository_name}: {e}")
    except OSError as e:
        if e.errno == 36:  # Filename too long
            print(f"Error: Filename too long in repository {repository_name} for commit {commit_sha}")

    
    

def calculate_tlocs(repository_name: str, rc_commit_sha: str, prev_commit_sha: str):
    
    if rc_commit_sha == prev_commit_sha:
        raise ValueError("RC and previous commit SHAs must be different")
    
    rc_loc = get_loc(repository_name, rc_commit_sha)
    prev_loc = get_loc(repository_name, prev_commit_sha)
    
    if rc_loc is None or prev_loc is None:
        raise ValueError("Could not calculate LOC for one of the commits")

    return rc_loc - prev_loc