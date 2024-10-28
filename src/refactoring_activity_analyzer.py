import aiofiles
import asyncio
import json
import logging
import os
import re
import subprocess
from aiohttp import ClientSession
from datetime import datetime
from pathlib import Path

from util import LogLevel, log_and_print


async def count_commit_types(file, logger, semaphore):
    try:
        async with semaphore:
            async with aiofiles.open(file, "r") as f:
                repo_name = Path(file).stem
                file_content = await f.read()
                data = json.loads(file_content)
                if data:
                    types = {}
                    shas = []

                    log_and_print(
                        logger,
                        LogLevel.INFO,
                        f"Collecting RepositoryMiner data from {repo_name}...",
                    )

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

                    log_and_print(
                        logger,
                        LogLevel.INFO,
                        f"Found {len(sorted_types)} different refactoring types from {repo_name}",
                    )

                    return {
                        "repository": repo_name,
                        "refactoring_types": sorted_types,
                        "shas": shas,
                    }

    except json.JSONDecodeError:
        log_and_print(logger, LogLevel.ERROR, f"{file} is invalid JSON, skipping")
        return {}

    except FileNotFoundError:
        log_and_print(logger, LogLevel.ERROR, f"Error: File {file} not found")
        return {}

    except Exception as e:
        log_and_print(logger, LogLevel.ERROR, f"Unexpected error occurred: {e}")
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
    hours = int(avg // 3600)

    return f"{hours} hours, which is ~{days} days"


async def analyze(cloned_repositories_dir, semaphore):
    logger = logging.getLogger("refactoring_activity_analyzer_logger")
    dest_dir = "results/refactoring_activity"
    os.makedirs(dest_dir, exist_ok=True)

    files = [
        (f.path, f.name)
        for f in os.scandir("results/miner_results")
        if f.is_file() and f.name.endswith(".json")
    ]

    if len(files) < 1:
        log_and_print(logger, LogLevel.INFO, "RepositoryMiner results not found")
        return

    async with ClientSession() as session:
        log_and_print(
            logger, LogLevel.INFO, "Refactoring Activity Analyzer is starting"
        )

        results = await asyncio.gather(
            *(count_commit_types(file[0], logger, semaphore) for file in files)
        )

        log_and_print(
            logger,
            LogLevel.INFO,
            "Calculating AVG inter-refactoring times for repositories...",
        )

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

        filename = f"{dest_dir}/refactoring_type_results.json"

        with open(filename, "a") as file:
            file.truncate(0)
            json.dump(results, file)

    log_and_print(
        logger,
        LogLevel.INFO,
        f"Refactoring activity analyzer is finished\nActivity analyzer results are in {dest_dir}/refactoring_type_results.json",
    )
