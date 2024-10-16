import asyncio
import os


async def clone(directory, run_subcommand):
    clone_commands = []

    with open("results/ok_repos.txt", "r") as file:
        repositories = file.readlines()

        os.chdir(directory)

        for index in range(10):
            command = f"git clone {repositories[index]}"
            clone_commands.append(command)

        await asyncio.gather(*[run_subcommand(command) for command in clone_commands])
