import asyncio
import os
import configparser

import refactoring_activity_analyzer
import refactoring_miner
import repository_cloner
import repository_fetcher


async def main():
    config = configparser.ConfigParser()
    config.read("config.ini")

    csv_file = config["files"]["csv_file"]
    cloned_repositories_dir = config["paths"]["cloned_repositories_dir"]
    refactoring_miner_exec = config["executables"]["refactoring_miner_exec"]
    github_apikey = config["keys"]["github_apikey"]

    envs = {
        "csv_file": csv_file,
        "cloned_repositories_dir": cloned_repositories_dir,
        "refactoring_miner_exec": refactoring_miner_exec,
        "github_apikey": github_apikey,
    }

    for key, path in envs.items():
        if len(path) < 5:
            print(f"Provide a proper value for {key} in config.ini")
            exit(1)

    os.makedirs(cloned_repositories_dir, exist_ok=True)

    # await repository_fetcher.get_repositories(csv_file)
    # await repository_cloner.clone(cloned_repositories_dir)
    # refactoring_miner.run_miner(cloned_repositories_dir, refactoring_miner_exec)
    await refactoring_activity_analyzer.analyze(github_apikey)


asyncio.run(main())
