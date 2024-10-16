import asyncio


async def clone(repositories, directory, run_subcommand):
    clone_commands = []

    for repo in repositories:
        command = f"git clone {repo}"
        clone_commands.append(command)

    await asyncio.gather(*[run_subcommand(command) for command in clone_commands])
