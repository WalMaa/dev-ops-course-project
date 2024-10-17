import asyncio
import os
import configparser

import analyzer
import refactoring_miner
import repository_cloner
import repository_fetcher


async def main():
    config = configparser.ConfigParser()
    config.read("config.ini")

    csv_file = config["files"]["csv_file"]
    cloned_repositories_dir = config["paths"]["cloned_repositories_dir"]
    refactoring_results_dir = config["paths"]["refactoring_results_dir"]
    refactoring_type_results_dir = config["paths"]["refactoring_type_results_dir"]

    paths = {
        "cloned_repositories_dir": cloned_repositories_dir,
        "refactoring_results_dir": refactoring_results_dir,
        "refactoring_type_results_dir": refactoring_type_results_dir,
    }

    for key, path in paths.items():
        if len(path) < 5:
            print(f"Provide a proper directory for {key} in config.ini")
            exit(1)

    for path in paths.values():
        os.makedirs(path, exist_ok=True)

    await repository_fetcher.get_repositories(csv_file)
    await repository_cloner.clone(cloned_repositories_dir)
    refactoring_miner.run_miner(cloned_repositories_dir, refactoring_results_dir)
    await analyzer.analyze(refactoring_results_dir, refactoring_type_results_dir)


asyncio.run(main())
