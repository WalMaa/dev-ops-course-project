import asyncio
import os


async def run_miner(repo_path, miner_result_directory, run_subcommand):
    repository_directories = [
        (f.path, f.name) for f in os.scandir(repo_path) if f.is_dir()
    ]
    refactoring_commands = []

    for dir_path, dir_name in repository_directories:
        command = f"RefactoringMiner -a {dir_path} -json {miner_result_directory}{dir_name}.json"
        refactoring_commands.append(command)

    await asyncio.gather(*[run_subcommand(command) for command in refactoring_commands])
