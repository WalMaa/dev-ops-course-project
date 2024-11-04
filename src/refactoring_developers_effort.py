import subprocess
import tempfile
import os
import json

"""
This module is responsible for calculating the touched lines of code for each refactoring and each developer effort. Task E in the project handout
"""

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
    await process_file(files[0][0])
    
    
async def process_file(file_path : str):
    """Processes a single refactoring results file.

    Args:
        file_path (str): local path to the refactoring results file
    """
    print(f"Processing file: {file_path}")

    with open(file_path, "r") as file:
        refactoring_results = json.load(file)
        
    commits = refactoring_results["commits"]
        
    print(commits)

    for index, commit in enumerate(commits):
        print(commit)
        if len(commit["refactorings"]) == 0:
            continue
        if index + 1 < len(commits):
            calculate_tlocs(commit["repository"], commit["sha1"], commits[index + 1]["sha1"])

    
def get_loc(repository_url: str, commit_sha: str):
    """
    Get the lines of code (LOC) for a given commit using the scc tool.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        
        subprocess.run(["git", "clone", repository_url], check=True)
        subprocess.run(["git", "checkout", commit_sha], check=True, cwd=temp_dir)
        
        result = subprocess.run(["scc"], capture_output=True, text=True)
        
        # Parse the output to get the total lines of code
        loc = 0
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) > 3 and parts[0].isdigit():
                loc += int(parts[2])  # Assuming the third column is the LOC
                
        
    return loc

def calculate_tlocs(repository_url: str, rc_commit_sha: str, prev_commit_sha: str):
    """
    Calculate the total count of touched lines of code (TLOCs) for each refactoring and each developer.
    """

    # Get the LOC for the refactoring commit (RC)
    rc_loc = get_loc(repository_url, rc_commit_sha)

    # Get the LOC for the previous commit
    prev_loc = get_loc(repository_url, prev_commit_sha)

    # Calculate the TLOC as the absolute difference between both numbers
    tloc = abs(rc_loc - prev_loc)

    print(f"Refactoring Commit (RC): {rc_commit_sha}")
    print(f"Previous Commit: {prev_commit_sha}")
    print(f"TLOC: {tloc}")