import asyncio
import logging
import os
import pandas as pd
import re
from aiohttp import ClientSession, ClientError, ClientTimeout

from util import LogLevel, log_and_print


def get_github_urls(filename, logger):
    df = pd.read_csv(filename, low_memory=False, dtype={7: str, 8: str})
    col_headers = list(df.columns)
    github_urls = []

    if "project" in col_headers and "organization" in col_headers:
        for index, row in df.iterrows():
            project = row["project"]
            organization = row["organization"]

            modified_row = (
                project.removeprefix(f"{organization}_")
                # replacing some common keywords
                .replace("-master", "")
                .replace("-builder", "")
                .replace("-parent", "")
                # lastly, remove the organization from the beginning
                .removeprefix(f"{organization}-")
            )

            url = f"https://github.com/{organization}/{modified_row}"
            if url not in github_urls:
                github_urls.append(url)
                log_and_print(logger, LogLevel.INFO, f"Found URL: {url}")
    else:
        log_and_print(
            logger,
            LogLevel.ERROR,
            "The source csv file does not contain expected headers 'project' and 'organization'",
        )

    return github_urls


async def get_http_statuses_for_urls(session, urls, logger, semaphore):
    tasks = [test_http_status(session, url, logger, semaphore) for url in urls]
    return await asyncio.gather(*tasks)


async def test_http_status(session, url, logger, semaphore):
    try:
        async with semaphore:
            async with session.get(url, timeout=ClientTimeout(total=60)) as response:
                log_and_print(logger, LogLevel.INFO, f"{url} {response.status}")
                return f"{url} {response.status}"

    except asyncio.TimeoutError:
        log_and_print(logger, LogLevel.INFO, f"{url} caused timeout")
        return f"{url} 408"

    except ClientError as error:
        log_and_print(logger, LogLevel.INFO, f"Request failed for {url}: {str(error)}")
        return f"{url} request failed"


def write_to_text_file(collection, filepath):
    with open(filepath, "a") as file:
        file.truncate(0)
        for item in collection:
            file.write(f"{item}{'\n'}")


def write_to_text_file_and_print(collection, filepath, header, logger):
    with open(filepath, "a") as file:
        file.truncate(0)

        log_and_print(logger, LogLevel.INFO, f"\n{header}")

        if len(collection) > 0:
            for item in collection:
                file.write(f"{item}\n")
                log_and_print(logger, LogLevel.INFO, item)
        else:
            log_and_print(logger, LogLevel.INFO, "None!")


async def run_subcommand(cmd, logger, semaphore):
    async with semaphore:
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        log_and_print(logger, LogLevel.INFO, f"[{cmd!r} exited with {proc.returncode}]")
        if stdout:
            log_and_print(logger, LogLevel.INFO, f"[stdout]\n{stdout.decode()}")
        if stderr:
            log_and_print(logger, LogLevel.ERROR, f"[stderr]\n{stderr.decode()}")


def convert_ssh_to_https(ssh_urls):
    https_urls = []

    for url in ssh_urls:
        result = url.replace("git@github.com:", "https://github.com/")
        https_urls.append(result)

    return https_urls


def convert_https_to_ssh(https_urls):
    ssh_urls = []

    for url in https_urls:
        result = url.replace("https://github.com/", "git@github.com:")
        ssh_urls.append(result)

    return ssh_urls


async def get_repositories(csv_file, semaphore):
    logger = logging.getLogger("repository_fetcher_logger")
    https_urls = get_github_urls(csv_file, logger)
    ssh_urls = convert_https_to_ssh(https_urls)
    dest_dir = "results/repo_lists"
    os.makedirs(dest_dir, exist_ok=True)
    http_statuses = []
    ok_repos = []
    unavailable_repos = []

    write_to_text_file_and_print(
        ssh_urls, f"{dest_dir}/ssh_urls.txt", "All repositories:", logger
    )

    # Test the http responses of the github urls, eg. 200, 301, 400
    async with ClientSession() as session:
        print("\nHTTP statuses of the repositories:")
        http_statuses = await get_http_statuses_for_urls(
            session, https_urls, logger, semaphore
        )

    write_to_text_file(http_statuses, f"{dest_dir}/https_statuses.txt")

    # Sort the received http responses to 200 OK and 301/400 NOT OK
    for status in http_statuses:
        if "200" in status:
            stripped_status = re.sub(r" \d+$", "", status)
            ok_repos.append(stripped_status)
        else:
            stripped_status = re.sub(r" \d+$", "", status)
            unavailable_repos.append(stripped_status)

    write_to_text_file(
        sorted(convert_https_to_ssh(ok_repos), key=str.casefold),
        f"{dest_dir}/ok_repos.txt",
    )

    write_to_text_file_and_print(
        sorted(unavailable_repos, key=str.casefold),
        f"{dest_dir}/unavailable_repos.txt",
        "Unavailable repositories:",
        logger,
    )

    count_ok = len(ok_repos)
    count_unavailable = len(unavailable_repos)

    log_and_print(
        logger,
        LogLevel.INFO,
        f"""\nRepository fetcher is finished."""
        f"""\nFound {count_ok} OK repositories and"""
        f""" {count_unavailable} unavailable repositories."""
        f"""\nOk repos are in {dest_dir}/ok_repos.txt"""
        f"""\nUnavailable repos are in {dest_dir}/unavailable_repos.txt""",
    )
