import asyncio
from pathlib import Path
import re
import subprocess
from datetime import datetime
from aiohttp import ClientSession
import json
import aiofiles
import os


def is_proper_json(data):
    try:
        json.loads(data)
    except ValueError:
        return False
    return True


async def count_commit_types(file):
    try:
        async with aiofiles.open(file, "r") as f:
            repo_name = Path(file).stem
            data = await f.read()
            if is_proper_json(data):
                data = json.loads(data)

                types = {}
                shas = []

                for commit in data["commits"]:
                    for refactoring in commit.get("refactorings", []):
                        commit_type = refactoring.get("type")
                        if commit_type:
                            if commit_type in types:
                                types[commit_type] += 1
                            else:
                                types[commit_type] = 1

                    sha = commit.get("sha1")
                    if sha:
                        shas.append(sha)

                sorted_types = [
                    {"type": commit_type, "count": count}
                    for commit_type, count in sorted(
                        types.items(), key=lambda item: item[1], reverse=True
                    )
                ]

                return {
                    "repository": repo_name,
                    "refactoring_types": sorted_types,
                    "shas": shas,
                }

    except FileNotFoundError:
        print(f"Error: File {file} not found")
        return {}

    except json.JSONDecodeError:
        print(f"Error: File {file} is not valid JSON")
        return {}

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return {}


async def get_avg_inter_refactoring_times(
    session, commit_ids, repo_name, cloned_repositories_dir
):
    path = os.path.join(cloned_repositories_dir, repo_name)

    sp_result = subprocess.run(
        ["git", "-C", path, "log", "--pretty=format:%H %cd"],
        capture_output=True,
        text=True,
    )

    git_log_commits = sp_result.stdout
    git_log_iter = git_log_commits.splitlines()
    dates = []

    # Check whether the commit matches with a commit
    # recognized as a refactoring
    for id in commit_ids:
        for line in git_log_iter:
            if id in line:
                date = re.sub(r"^[^ ]* ", "", line)
                dates.append(date)

    return dates


def calculate_avg_time_diff(times):
    time_differences = []
    datetime_objects = [datetime.strptime(t, "%a %b %d %H:%M:%S %Y %z") for t in times]

    for index in range(len(datetime_objects) - 1):
        diff = (datetime_objects[index + 1] - datetime_objects[index]).total_seconds()
        time_differences.append(diff)

    avg = abs(sum(time_differences) / len(time_differences))

    days = int(avg // 86400)
    hours = int((avg % 86400) // 3600)
    minutes = int((avg % 3600) // 60)
    seconds = avg % 60

    return f"{days} days, {hours} hours, {minutes} minutes, {seconds:.2f} seconds"


async def analyze(cloned_repositories_dir):
    files = [
        (f.path, f.name)
        for f in os.scandir("results/miner_results")
        if f.is_file() and f.name.endswith(".json")
    ]

    os.makedirs("results", exist_ok=True)
    os.makedirs("results/part_c", exist_ok=True)

    async with ClientSession() as session:
        results = await asyncio.gather(*(count_commit_types(file[0]) for file in files))

        for repository in results:
            if repository:
                dates = await get_avg_inter_refactoring_times(
                    session,
                    repository.get("shas"),
                    repository.get("repository"),
                    cloned_repositories_dir,
                )
                if dates:
                    time_diff = calculate_avg_time_diff(dates)
                    del repository["shas"]
                    repository["avg_commit_time_diff"] = time_diff

        filename = "results/part_c/refactoring_type_results.json"

        with open(filename, "a") as file:
            file.truncate(0)
            json.dump(results, file)
