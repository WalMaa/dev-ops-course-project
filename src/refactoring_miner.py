import os
import re
import asyncio
import logging

from util import LogLevel, log_and_print


async def __handle_stream(stream, logger, log_level):
    line = await stream.readline()

    while line:
        line_content = line.decode().strip()

        if "Processing" in line_content:
            stripped_line = re.search(r"([^\/]*$)", line_content)
            if stripped_line:
                repo_and_commit = stripped_line.group(0).rstrip("...").strip()
                hash = re.search(r"\b[0-9a-f]{40}\b", repo_and_commit)
                if hash:
                    log_and_print(logger, log_level, f"Mining commit {repo_and_commit}")
        elif "Analyzed" in line_content:
            finished_repository = re.sub(r"^.*Analyzed\s", "", line_content)
            log_and_print(logger, log_level, f"Finished mining {finished_repository}")
        else:
            if "Total count:" not in line_content:
                log_and_print(logger, log_level, line.decode().strip())

        line = await stream.readline()


async def run_subcommand(cmd_with_name, logger, semaphore):
    cmd, name = cmd_with_name

    async with semaphore:
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        log_and_print(logger, LogLevel.INFO, f"Mining {name}")

        await asyncio.gather(
            __handle_stream(proc.stdout, logger, LogLevel.INFO),
            # Miner seems to direct output to stderr instead of stdout
            __handle_stream(proc.stderr, logger, LogLevel.INFO),
        )

        await proc.wait()
        return proc.returncode


async def run_miner(repo_path, executable, semaphore):
    logger = logging.getLogger("miner_logger")
    dest_dir = "results/miner_results"
    os.makedirs(dest_dir, exist_ok=True)

    repository_directories = [
        (f.path, f.name) for f in (os.scandir(repo_path)) if f.is_dir()
    ]

    commands_and_names = []

    for dir_path, dir_name in repository_directories:
        command = (
            f"{executable} -a {dir_path} -json results/miner_results/{dir_name}.json"
        )
        commands_and_names.append((command, dir_name))

    tasks = [
        asyncio.create_task(run_subcommand(command, logger, semaphore))
        for command in commands_and_names
    ]

    total_commands = len(commands_and_names)
    successful_commands = 0
    failed_commands = 0

    for future in asyncio.as_completed(tasks):
        result = await future

        if result == 0:
            successful_commands += 1
        else:
            failed_commands += 1

        if successful_commands > 0:
            log_and_print(
                logger,
                LogLevel.INFO,
                f"{successful_commands} minings successful of total {total_commands}",
            )

        if failed_commands > 0:
            log_and_print(
                logger,
                LogLevel.WARNING,
                f"{failed_commands} minings failed of total {total_commands}",
            )

    log_and_print(
        logger,
        LogLevel.INFO,
        f"Refactoring miner is finished\nMiner results are in {dest_dir} directory",
    )
