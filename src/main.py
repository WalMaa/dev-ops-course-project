import asyncio
import logging
import os
import configparser
from datetime import datetime
from multiprocessing import cpu_count

import refactoring_activity_analyzer
import refactoring_miner
import repository_cloner
import repository_fetcher
import refactoring_tlocs
import repository_pydriller
import fetch_github_issues
import fetch_jira_issues
from util import LogLevel, log_and_print


async def main():
    logger = logging.getLogger("main")
    config = configparser.ConfigParser()
    config.read("config.ini")

    csv_file = config["files"]["csv_file"]
    cloned_repositories_dir = config["paths"]["cloned_repositories_dir"]
    refactoring_miner_exec = config["executables"]["refactoring_miner_exec"]

    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    logging.basicConfig(
        filename=f"logs/log_{timestamp}.log", encoding="utf-8", level=logging.DEBUG
    )

    envs = {
        "csv_file": csv_file,
        "cloned_repositories_dir": cloned_repositories_dir,
        "refactoring_miner_exec": refactoring_miner_exec,
    }

    for key, path in envs.items():
        if len(path) < 5:
            print(f"Provide a proper value for {key} in config.ini")
            exit(1)

    os.makedirs(cloned_repositories_dir, exist_ok=True)
    os.makedirs("results", exist_ok=True)

    cpus = cpu_count()
    max_procs = max(1, cpus // 2)
    semaphore = asyncio.Semaphore(max_procs)

    log_and_print(
        logger,
        LogLevel.INFO,
        f"""CPU count on this machine is {cpus}\n"""
        f"""Limiting the no. of async operations to {max_procs} to optimize performance""",
    )

    # Comment / uncomment the rows below based on what you want to do
    await repository_fetcher.get_repositories(csv_file, semaphore)
    await repository_cloner.clone(
        cloned_repositories_dir,
    )
    await refactoring_miner.run_miner(
        cloned_repositories_dir, refactoring_miner_exec, semaphore
    )
    await refactoring_activity_analyzer.analyze(cloned_repositories_dir, semaphore)
    repository_pydriller.run_pydriller(cloned_repositories_dir)
    await refactoring_tlocs.calculate("./results/miner_results")

    fetch_github_issues.categorize_repos_by_issues_status("./results/repo_lists/ok_repos.txt")
    await fetch_github_issues.fetch_issues_from_repos_in_file("./results/issues/github_issues_enabled.txt")
    await fetch_jira_issues.fetch_and_save_issues("./results/issues", "github_issues_disabled.txt")

if __name__ == "__main__":
    asyncio.run(main())

