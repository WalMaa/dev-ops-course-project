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

async def calculate(refactoring_results_dir):
    print("developer effort calculation")
    
    files = [
        (f.path, f.name)
        for f in os.scandir(refactoring_results_dir)
        if f.is_file() and f.name.endswith(".json")
    ]
    
    if len(files) < 1:
        print("Refactoring results not found")
        return
    await process_file(files[0][0], files[0][1])
    
    
async def process_file(file_path : str, file_name : str):
    """Processes a single refactoring results file.

    Args:
        file_path (str): local path to the refactoring results file
    """
    
    repository_name = file_name.replace(".json", "")
    
    print(f"Processing file: {file_path}")

    with open(file_path, "r") as file:
        refactoring_results = json.load(file)
        
    commits = refactoring_results["commits"]
        
    for index, commit in enumerate(commits):
        if len(commit["refactorings"]) == 0:
            continue
        if index + 1 < len(commits):
            calculate_tlocs(repository_name, commit["sha1"], commits[index + 1]["sha1"])

    
def get_loc(repository_name: str, commit_sha: str):
    """
    Get the lines of code (LOC) for a given commit using the scc tool.
    """
    subprocess.run(["git", "checkout", commit_sha], check=True, cwd=cloned_repositories_dir + "/" + repository_name)
    
    result = subprocess.run(["scc"], capture_output=True, text=True, cwd=cloned_repositories_dir + "/" + repository_name)
    
    # Parse the output to get the total lines of code
    loc = 0
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) > 3 and parts[0].isdigit():
            loc += int(parts[2])  # Assuming the third column is the LOC
                
        
    return loc

def calculate_tlocs(repository_name: str, rc_commit_sha: str, prev_commit_sha: str):
    """
    Calculate the total count of touched lines of code (TLOCs) for each refactoring and each developer.
    """

    # Get the LOC for the refactoring commit (RC)
    rc_loc = get_loc(repository_name, rc_commit_sha)

    # Get the LOC for the previous commit
    prev_loc = get_loc(repository_name, prev_commit_sha)

    # Calculate the TLOC as the absolute difference between both numbers
    tloc = abs(rc_loc - prev_loc)

    print(f"Refactoring Commit (RC): {rc_commit_sha}")
    print(f"Previous Commit: {prev_commit_sha}")
    print(f"TLOC: {tloc}")