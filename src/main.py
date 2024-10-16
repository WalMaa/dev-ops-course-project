import asyncio

import refactoring_miner
import repository_cloner
import repository_fetcher


async def run_subcommand(cmd):
    print(f"Executing command: {cmd}")
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    print(f"[{cmd!r} exited with {proc.returncode}]")
    if stdout:
        print(f"[stdout]\n{stdout.decode()}")
    if stderr:
        print(f"[stderr]\n{stderr.decode()}")
    if not stdout and not stderr:
        print(f"No output for command: {cmd!r} (return code: {proc.returncode})")


async def main():
    # TODO: Use the text files as input instead to allow calling for modules separately
    repository_dir = "/home/kristian/devops_repositories/"
    repos_to_clone = await repository_fetcher.get_repositories("sonar_measures.csv")
    await repository_cloner.clone(repos_to_clone, repository_dir, run_subcommand)
    await refactoring_miner.run_miner(
        repository_dir, "/home/kristian/refactoringminer_results/", run_subcommand
    )


asyncio.run(main())
