import asyncio
import logging

from util import LogLevel, log_and_print


async def run_subcommand(
    cmd,
    logger,
):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await proc.communicate()
        if stdout:
            log_and_print(logger, LogLevel.INFO, f"{stdout.decode()}")
        if stderr:
            # Git seems to direct output to stderr instead of stdout
            log_and_print(logger, LogLevel.INFO, f"{stderr.decode()}")
    except asyncio.TimeoutError:
        proc.kill()
        log_and_print(logger, LogLevel.ERROR, f"{cmd!r} timed out and was killed")
    except Exception as e:
        log_and_print(logger, LogLevel.ERROR, f"Error running command {cmd!r}: {e}")

    await proc.wait()
    return proc.returncode


async def clone(directory):
    logger = logging.getLogger("cloner_logger")
    clone_commands = []

    with open("results/repo_lists/ok_repos.txt", "r") as file:
        repositories = file.readlines()

        # Matti: range(0, 87)
        # Kristian: range(30, 179)
        # Arttu: range(180, 269)
        # Walter: range(270, len(repositories) -1)
        for index in range(30, 179):
            command = f"git -C {directory} clone {repositories[index]}"
            clone_commands.append(command)

    count_of_clone_ops = len(clone_commands)
    log_and_print(
        logger, LogLevel.INFO, f"Starting cloning {count_of_clone_ops} repositories"
    )

    tasks = [
        asyncio.create_task(run_subcommand(command, logger))
        for command in clone_commands
    ]

    successful_clones = 0
    failed_clones = 0

    for future in asyncio.as_completed(tasks):
        result = await future

        if result == 0:
            successful_clones += 1
        else:
            failed_clones += 1

    log_and_print(
        logger,
        LogLevel.INFO,
        """Cloner is finished"""
        f"""\nSuccessfully cloned {successful_clones} repositories """
        f"""\nFailed to clone {failed_clones} repositories """,
    )
