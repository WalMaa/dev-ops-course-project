import requests
import json
import time
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable not set")

headers = {"Authorization": f"token {GITHUB_TOKEN}"}

def check_if_issues_enabled(repo_url):
    parts = repo_url.strip().split(":")[-1].replace(".git", "").split("/")
    owner = parts[0]
    repo = parts[1]

    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        repo_data = response.json()
        return repo_data.get("has_issues", False)
    elif response.status_code == 403:
        print("Rate limit reached or access denied. Waiting for 60 seconds before retrying...")
        time.sleep(5)  # Wait for 5 seconds before retrying
        return check_if_issues_enabled(repo_url)  # Retry after delay
    else:
        print(f"Failed to fetch data for {repo_url}: {response.status_code}")
        return None

def categorize_repos_by_issues_status(file_path):
    issues_enabled = []
    issues_disabled = []

    # Open and read the text file
    with open(file_path, "r") as txt_file:
        for line in txt_file:
            repo_url = line.strip()  # Remove any leading/trailing whitespace
            if repo_url:  # Check if the line is not empty
                result = check_if_issues_enabled(repo_url)
                if result is True:
                    issues_enabled.append(repo_url)
                elif result is False:
                    issues_disabled.append(repo_url)
                else:
                    print(f"Could not determine issue tracking status for {repo_url}.")

    # Write results to text files
    os.makedirs("./results/issues", exist_ok=True)
    with open("./results/issues/github_issues_enabled.txt", "w") as enabled_file:
        for url in issues_enabled:
            enabled_file.write(url + "\n")

    with open("./results/issues/github_issues_disabled.txt", "w") as disabled_file:
        for url in issues_disabled:
            disabled_file.write(url + "\n")

    print("Results saved to 'github_issues_enabled.txt' and 'github_issues_disabled.txt'.")

def fetch_all_issues(owner, repo):
    issues = []
    page = 1
    while True:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        params = {"state": "all", "page": page, "per_page": 1000}  # Fetch 1000 issues per page
        response = requests.get(api_url, headers=headers, params=params)

        if response.status_code == 200:
            page_issues = response.json()
            if not page_issues:
                break  # Exit if no more issues on this page
            issues.extend(page_issues)
            page += 1
        elif response.status_code == 403:
            print("Rate limit reached while fetching issues. Waiting for 60 seconds before retrying...")
            time.sleep(60)  # Wait and retry
        else:
            print(f"Failed to fetch issues for {owner}/{repo}: {response.status_code}")
            break
    
    # Save issues to a JSON file named after the repository
    if issues:
        os.makedirs("./results/issues/github_issues", exist_ok=True)
        file_path = f"./results/issues/github_issues/{owner}_{repo}_issues.json"
        with open(file_path, "w") as file:
            json.dump(issues, file, indent=4)
        print(f"Issues saved to {file_path}")
    else:
        print(f"No issues found for {owner}/{repo}")

def fetch_issues_from_repos_in_file(file_path):
    with open(file_path, "r") as txt_file:
        for line in txt_file:
            repo_url = line.strip()
            if repo_url:
                has_issues = check_if_issues_enabled(repo_url)
                if has_issues:
                    # Extract owner and repo name from the SSH URL
                    parts = repo_url.strip().split(":")[-1].replace(".git", "").split("/")
                    owner = parts[0]
                    repo = parts[1]
                    print(f"Fetching issues for {owner}/{repo}...")
                    fetch_all_issues(owner, repo)
                else:
                    print(f"{repo_url} does not have issues enabled.")