import asyncio
import configparser

import refactoring_miner
import repository_cloner
import repository_fetcher


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


async def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
    csv_dir = config["paths"]["csv_dir"]
    cloned_repositories_dir = config["paths"]["cloned_repositories_dir"]
    refactoring_results_dir = config["paths"]["refactoring_results_dir"]

    await repository_fetcher.get_repositories(csv_dir)
    await repository_cloner.clone(cloned_repositories_dir, run_subcommand)
    await refactoring_miner.run_miner(
        cloned_repositories_dir,
        refactoring_results_dir,
        run_subcommand,
    )


asyncio.run(main())
