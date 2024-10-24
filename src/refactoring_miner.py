import os
from pathlib import Path
import json
import concurrent.futures
from multiprocessing import cpu_count
import subprocess


def run_miner_subcommand(cmd):
    try:
        print(f"\nStarted mining: {cmd}")

        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=900,
        )

        print(result.stdout)
        print(result.stderr, end="")
        return result.returncode

    except subprocess.TimeoutExpired:
        print(f"{cmd} timed out")
        return -1


def run_miner(repo_path, executable):
    refactoring_commands = []
    commands_finished = 0
    commands_failed = 0
    repository_directories = [
        (f.path, f.name) for f in os.scandir(repo_path) if f.is_dir()
    ]

    os.makedirs("results", exist_ok=True)
    os.makedirs("results/miner_results", exist_ok=True)

    for dir_path, dir_name in repository_directories:
        command = (
            f"{executable} -a {dir_path} -json results/miner_results/{dir_name}.json"
        )
        refactoring_commands.append(command)

    count_of_commands = len(refactoring_commands)
    workers = max(2, cpu_count())

    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for result in executor.map(run_miner_subcommand, refactoring_commands):
            return_code = result

            if return_code != 0:
                commands_failed += 1
            else:
                commands_finished += 1
                print(f"\n{commands_finished} refactorings done of {count_of_commands}")
                print(f"{commands_failed} refactorings failed of {count_of_commands}")

    failed_repositories = []

    for entry in os.scandir("results/miner_results"):
        if entry.is_file():
            with open(entry, "r") as file:
                content = file.read()
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    failed_repositories.append(Path(entry).stem)

    if len(failed_repositories) > 0:
        print("\nFailed to mine following repositories:")
        for repo in failed_repositories:
            print(repo)

    print("\nRefactoring miner is finished")
