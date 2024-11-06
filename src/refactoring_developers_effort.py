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

async def calculate(refactoring_results_dir):
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
    for file in files:
        await process_file(file[0], file[1])
        
    
    
async def process_file(file_path : str, file_name : str):
    """Processes a single refactoring results file.

    Args:
        file_path (str): local path to the refactoring results file
    """
    
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
            tlocs = calculate_tlocs(repository_name, commit["sha1"], commits[index + 1]["sha1"]) 
            commit_results.append({"commit": commit["sha1"], "tlocs": tlocs})   
            
    with open(f"{dest_dir}/{repository_name}.json", "w", encoding="utf-8") as file:
        json.dump({"repository": repository_name,
                   "refactorings": commit_results}, file)

    
def get_loc(repository_name: str, commit_sha: str):
    repo_dir = os.path.join(cloned_repositories_dir, repository_name)
    lock_file = os.path.join(repo_dir, ".git", "index.lock")
    
    if os.path.exists(lock_file):
        os.remove(lock_file)
    
    subprocess.run(["git", "checkout", "-f", commit_sha], capture_output=False,  check=True, cwd=repo_dir)
    
    result = subprocess.run(["scc", "--no-cocomo", "--no-complexity", "--no-size"], encoding="utf-8",  capture_output=True, text=True, cwd=repo_dir)
    # print("SCC Result", result.stdout)
    
    # Parse the output to get the total lines of code
    loc = 0
    for line in result.stdout.splitlines():
        parts = line.split()
        print(parts)
        if (len(parts) > 1 and parts[0] == "Total"):
            loc = int(parts[2])
                
    print(f"LOC for commit {commit_sha}: {loc}")
    return loc

def calculate_tlocs(repository_name: str, rc_commit_sha: str, prev_commit_sha: str):
    
    if rc_commit_sha == prev_commit_sha:
        raise ValueError("RC and previous commit SHAs must be different")
    
    print(f"Calculating TLOCs for {repository_name} between {rc_commit_sha} and {prev_commit_sha}")
    
    """
    Calculate the total count of touched lines of code (TLOCs) for each refactoring and each developer.
    """

    # Get the LOC for the refactoring commit (RC)
    rc_loc = get_loc(repository_name, rc_commit_sha)

    # Get the LOC for the previous commit
    prev_loc = get_loc(repository_name, prev_commit_sha)

    return rc_loc - prev_loc