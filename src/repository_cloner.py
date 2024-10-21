import asyncio
import os


async def run_subcommand(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await proc.communicate()
        if stdout:
            print(f"{stdout.decode()}")
        if stderr:
            print(f"{stderr.decode()}")
    except asyncio.TimeoutError:
        proc.kill()
        print(f"{cmd!r} timed out and was killed")
    except Exception as e:
        print(f"Error running command {cmd!r}: {e}")


async def clone(directory):
    clone_commands = []

    with open("results/repo_lists/ok_repos.txt", "r") as file:
        repositories = file.readlines()

        os.chdir(directory)

        # Matti: range(0, 87)
        # Kristian: range(88, 179)
        # Arttu: range(180, 269)
        # Walter: range(270, len(repositories) -1)
        for index in range(88, 179):
            command = f"git clone {repositories[index]}"
            clone_commands.append(command)

        await asyncio.gather(*(run_subcommand(command) for command in clone_commands))
