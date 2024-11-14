import requests
import json
import time
import os
import shutil
import re

# JIRA API endpoint for fetching all projects
url = "https://issues.apache.org/jira/rest/api/2/project"

def parse_repository_list(file_path, output_file):
    """
    Parse the list of repositories to extract cleaned, lowercase keywords separately.
    Stores the parsed names collection in a JSON file.
    """
    with open(file_path, 'r') as f:
        repositories = f.readlines()
        
    # Initialize a list to hold parsed names for each repository
    parsed_names_collection = []
    
    # Process each repository URL to extract keywords
    for repo in repositories:
        # Extract the last part of the URL, convert to lowercase, and remove special characters
        repo_name = repo.strip().split('/')[-1].lower()
        # Remove special characters, then split into separate words
        words = re.sub(r'[^a-z0-9\s]', ' ', repo_name).split()
        parsed_names_collection.append(words)
        
    # Save the parsed names collection to a JSON file
    with open(output_file, 'w') as f:
        json.dump(parsed_names_collection, f, indent=4)
        
    print(f"Parsed names collection saved to {output_file}")

def fetch_projects():
    """Fetch all JIRA projects, exclude 'ASFSITE', and return a list of dictionaries with 'key' and 'name'."""
    response = requests.get(url)
    
    if response.status_code == 200:
        projects = response.json()
        # Filter out projects with the key "ASFSITE"
        project_list = [
            {"key": project["key"], "name": project["name"]}
            for project in projects
            if project["key"] != "ASFSITE"
        ]
        return project_list
    else:
        print(f"Error fetching projects: HTTP {response.status_code}")
        print("Response content:", response.text)
        return []

def load_json_file(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def jaccard_similarity(set1, set2):
    """Calculate Jaccard similarity between two sets."""
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union != 0 else 0

def find_closest_match(parsed_names, projects_collection):
    """
    For each project in parsed names, find the closest match in projects_collection.
    Only the first three words of each parsed name are considered for matching,
    with priority given to matches on the first word.
    """
    closest_matches = {}

    for parsed_name in parsed_names:
        # Use only the first three words from parsed_name and give priority to the first word
        parsed_set = set(parsed_name[:3])  # Convert the first three words to a set for Jaccard calculation
        first_word = parsed_name[0] if parsed_name else None  # Extract the first word, if available
        best_match = None
        highest_similarity = 0
        
        for project in projects_collection:
            # Clean and split project name into set of words
            project_set = set(re.sub(r'[^a-z0-9\s]', ' ', project['name'].lower()).split())
            similarity = jaccard_similarity(parsed_set, project_set)
            
            # Check if the first word from parsed_name is in the project_set
            if first_word and first_word in project_set:
                similarity += 0.2  # Add a weight to prioritize first-word matches (adjust as needed)
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = project

        # Check if a match was found
        if best_match:
            closest_matches[" ".join(parsed_name)] = {
                "closest_project_name": best_match["name"],
                "closest_project_key": best_match["key"],
                "similarity_score": highest_similarity
            }
        else:
            closest_matches[" ".join(parsed_name)] = {
                "closest_project_name": "No match found",
                "closest_project_key": None,
                "similarity_score": 0
            }
        
    return closest_matches

def save_matches_to_file(matches, output_file):
    """Save the closest matches to a JSON file."""
    with open(output_file, 'w') as f:
        json.dump(matches, f, indent=4)
    print(f"Closest matches saved to {output_file}")

# JIRA API base URL for searching issues
BASE_URL = "https://issues.apache.org/jira/rest/api/2/search"
MAX_RESULTS = 10000  # Number of issues per page
RATE_LIMIT_WAIT = 1  # Time to wait between requests in seconds

def load_closest_matches(file_path):
    """Load the closest matches data from JSON."""
    with open(file_path, 'r') as f:
        return json.load(f)

def fetch_issues(project_key, start_at=0):
    """Fetch issues for a given project key using JIRA API, with pagination and progress tracking."""
    issues = []
    total_issues = None  # Will be set after the first request
    
    while True:
        url = f"{BASE_URL}?jql=project={project_key}&startAt={start_at}&maxResults={MAX_RESULTS}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            issues.extend(data["issues"])
            
            # Set the total number of issues only after the first request
            if total_issues is None:
                total_issues = data["total"]
                print(f"Total issues to fetch for project {project_key}: {total_issues}")
            
            # Show progress
            fetched_count = start_at + len(data["issues"])
            print(f"Fetched {fetched_count} of {total_issues} issues for project {project_key}")
            
            # Check if we've fetched all issues
            if fetched_count >= total_issues:
                break
            
            start_at += MAX_RESULTS
            time.sleep(RATE_LIMIT_WAIT)  # Rate limiting
        else:
            print(f"Error fetching issues for project {project_key}: HTTP {response.status_code}")
            print("Response content:", response.text)
            break
            
    return issues

def save_issues_to_file(project_name, issues, output_folder):
    """Save the issues for each project to a JSON file named after the project name."""
    # Use the project name, replacing spaces with underscores, as the file name
    file_name = f"{output_folder}/{project_name.replace(' ', '_')}_issues.json"
    with open(file_name, 'w') as f:
        json.dump(issues, f, indent=4)
    print(f"Issues for project {project_name} saved to {file_name}")

def fetch_and_save_issues(issues_folder_path, repo_list_file):
    
    parse_repository_list(f"{issues_folder_path}/{repo_list_file}", f"{issues_folder_path}/parsed_names_collection.json")

    projects = fetch_projects()
    if projects:
        # Store projects in a text file in JSON format
        with open(f"{issues_folder_path}/projects_collection.txt", "w") as file:
            json.dump(projects, file, indent=4)
        print("Project collection has been saved to projects_collection.txt")
    
    parsed_names_file = f'{issues_folder_path}/parsed_names_collection.json'
    projects_collection_file = f'{issues_folder_path}/projects_collection.txt'
    closest_matches_file = f'{issues_folder_path}/closest_matches.json'

    parsed_names = load_json_file(parsed_names_file)
    projects_collection = load_json_file(projects_collection_file)

    # Find closest matches and save to file
    closest_matches = find_closest_match(parsed_names, projects_collection)
    save_matches_to_file(closest_matches, closest_matches_file)
    
    # Fetching issues for all repositories
    
    # Load closest matches file
    closest_matches = load_closest_matches(closest_matches_file)

    # Dictionary to track processed project keys and associated project names
    processed_projects = {}

    save_issues_location = f'{issues_folder_path}/jira_issues'
    os.makedirs(save_issues_location, exist_ok=True)
    
    for parsed_name, project_info in closest_matches.items():
        project_key = project_info.get("closest_project_key")
        project_name = project_info.get("closest_project_name")
        
        if project_key:
            if project_key in processed_projects:
                # Skip download if this project key has already been processed
                print(f"Skipping download for {parsed_name} as issues for project key {project_key} are already saved.")
            else:
                # Fetch and save issues if this is the first time encountering the project key
                print(f"Fetching issues for project: {project_name} (Project Key: {project_key})")
                issues = fetch_issues(project_key)
                save_issues_to_file(project_name, issues, f"{issues_folder_path}/jira_issues")
                processed_projects[project_key] = project_name  # Track the processed project key
        else:
            print(f"No valid project key for {parsed_name}, skipping...")