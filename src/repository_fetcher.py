import pandas as pd
import re
import asyncio
from aiohttp import ClientSession, ClientError
import os


def get_github_urls(filename):
    df = pd.read_csv(filename, low_memory=False, dtype={7: str, 8: str})

    project_names = df["project"]

    project_names = project_names.apply(
        lambda project: project.removeprefix("apache_")
        .replace("-master", "")
        .removeprefix("apache-")
    )

    project_names = project_names.drop_duplicates()

    github_urls = []

    for project in project_names:
        url = f"https://github.com/apache/{project}"
        github_urls.append(url)

    return github_urls


async def get_http_statuses_for_urls(session, urls):
    tasks = [test_http_status(session, url) for url in urls]
    return await asyncio.gather(*tasks)


async def test_http_status(session, url):
    try:
        async with session.get(url) as response:
            print(f"{url} {response.status}")
            return f"{url} {response.status}"
    except ClientError as error:
        print(f"Request failed for {url}: {str(error)}")


def write_to_text_file(collection, filepath):
    with open(filepath, "a") as file:
        file.truncate(0)
        for item in collection:
            file.write(f"{item}{'\n'}")


def write_to_text_file_and_print(collection, filepath, header):
    with open(filepath, "a") as file:
        file.truncate(0)
        print(f"\n{header}")
        for item in collection:
            file.write(f"{item}\n")
            print(item)


async def run_subcommand(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    print(f"[{cmd!r} exited with {proc.returncode}]")
    if stdout:
        print(f"[stdout]\n{stdout.decode()}")
    if stderr:
        print(f"[stderr]\n{stderr.decode()}")


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


async def get_repositories(csv_file):
    https_urls = get_github_urls(csv_file)
    ssh_urls = convert_https_to_ssh(https_urls)
    os.makedirs("results", exist_ok=True)
    http_statuses = []
    ok_repos = []
    unavailable_repos = []

    # Write urls to a file
    write_to_text_file_and_print(ssh_urls, "results/ssh_urls.txt", "All repositories:")
    write_to_text_file_and_print(
        https_urls, "results/https_urls.txt", "All repositories:"
    )

    # Test the http responses of the github urls, eg. 200, 301, 400
    async with ClientSession() as session:
        print("\nHTTP statuses of the repositories:")
        http_statuses = await get_http_statuses_for_urls(session, https_urls)

    # Write the http results to a file
    write_to_text_file(http_statuses, "results/https_statuses.txt")

    # Sort the received http responses to 200 OK and 301/400 NOT OK
    for status in http_statuses:
        if "200" in status:
            stripped_status = re.sub(r" \d+$", "", status)
            ok_repos.append(
                stripped_status.replace("https://github.com/", "git@github.com:")
            )
        else:
            stripped_status = re.sub(r" \d+$", "", status)
            unavailable_repos.append(
                stripped_status.replace("https://github.com/", "git@github.com:")
            )

    # Write the available repos to a file
    write_to_text_file(ok_repos, "results/ok_repos.txt")
    print("\nOK repositories are available in ok_repos.txt file")

    # Write the unavailable repos to a file
    write_to_text_file_and_print(
        unavailable_repos, "results/unavailable_repos.txt", "Unavailable repositories:"
    )

    return ok_repos
