import os
import concurrent.futures
import subprocess


def run_subcommand(cmd):
    print(cmd)

    with subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ) as proc:
        for line in proc.stdout:
            print(line, end="")
        for line in proc.stderr:
            print(line, end="")

    return proc.returncode


def run_miner(repo_path, executable):
    print("Refactoring miner is running")
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

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(run_subcommand, cmd): cmd for cmd in refactoring_commands
        }

        for future in concurrent.futures.as_completed(futures):
            cmd = futures[future]
            try:
                return_code = future.result()
                print(f"{cmd} finished with: {return_code}")
                commands_finished += 1
                print(f"{commands_finished} refactorings done of {count_of_commands}")
            except Exception as e:
                commands_failed += 1
                print(f"{cmd} failed: {e}")
                print(
                    f"{commands_failed} refactorings failed in total of {count_of_commands}"
                )

    print("Refactoring miner is finished")
