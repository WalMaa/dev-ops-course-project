import os
import concurrent.futures


def run_subcommand(cmd):
    print(cmd)
    proc = os.system(cmd)
    return proc


def run_miner(repo_path, miner_result_directory):
    repository_directories = [
        (f.path, f.name) for f in os.scandir(repo_path) if f.is_dir()
    ]
    refactoring_commands = []

    for dir_path, dir_name in repository_directories:
        command = f"RefactoringMiner -a {dir_path} -json {miner_result_directory}/{dir_name}.json"
        refactoring_commands.append(command)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for cmd in refactoring_commands:
            executor.submit(run_subcommand, cmd)

    print("Refactoring miner is finished")
