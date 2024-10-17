import asyncio
import os


async def run_subcommand(cmd):
    print(cmd)

    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await proc.communicate()
        print(f"{cmd!r} exited with {proc.returncode}")

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")
        if not stdout and not stderr:
            print(f"No output for command: {cmd!r} (return code: {proc.returncode})")
    except asyncio.TimeoutError:
        proc.kill()
        print(f"{cmd!r} timed out and was killed")
    except Exception as e:
        print(f"Error running command {cmd!r}: {e}")


async def clone(directory):
    clone_commands = []

    with open("results/ok_repos.txt", "r") as file:
        repositories = file.readlines()

        os.chdir(directory)

        for repository in repositories:
            command = f"git clone {repository}"
            clone_commands.append(command)

        await asyncio.gather(*(run_subcommand(command) for command in clone_commands))
