import os
import concurrent.futures


def run_subcommand(cmd):
    print(cmd)
    proc = os.system(cmd)
    return proc


def run_miner(repo_path, executable):
    repository_directories = [
        (f.path, f.name) for f in os.scandir(repo_path) if f.is_dir()
    ]
    refactoring_commands = []

    os.makedirs("results", exist_ok=True)
    os.makedirs("results/miner_results", exist_ok=True)

    for dir_path, dir_name in repository_directories:
        command = (
            f"{executable} -a {dir_path} -json results/miner_results/{dir_name}.json"
        )
        refactoring_commands.append(command)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for cmd in refactoring_commands:
            executor.submit(run_subcommand, cmd)

    print("Refactoring miner is finished")
