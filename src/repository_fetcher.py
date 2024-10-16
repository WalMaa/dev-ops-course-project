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


async def get_repositories(csv_file):
    urls = get_github_urls(csv_file)
    github_urls_filepath = "results/github_urls.txt"
    http_statuses_filepath = "results/http_statuses.txt"
    ok_repos_filepath = "results/ok_repos.txt"
    unavailable_repos_filepath = "results/unavailable_repos.txt"
    os.makedirs("results", exist_ok=True)
    http_statuses = []
    ok_repos = []
    unavailable_repos = []

    # Go through sonar_measures and format unique github urls
    write_to_text_file_and_print(urls, github_urls_filepath, "All repositories:")

    # Test the http responses of the github urls, eg. 200, 301, 400
    async with ClientSession() as session:
        print("\nHTTP statuses of the repositories:")
        http_statuses = await get_http_statuses_for_urls(session, urls)

    # Write the http results to a file
    write_to_text_file(http_statuses, http_statuses_filepath)

    # Sort the received http responses to 200 OK and 301/400 NOT OK
    for status in http_statuses:
        if "200" in status:
            stripped_status = re.sub(r" \d+$", "", status)
            ok_repos.append(stripped_status)
        else:
            stripped_status = re.sub(r" \d+$", "", status)
            unavailable_repos.append(stripped_status)

    # Write the available repos to a file
    write_to_text_file(ok_repos, ok_repos_filepath)
    print("\nOK repositories are available in ok_repos.txt file")

    # Write the unavailable repos to a file
    write_to_text_file_and_print(
        unavailable_repos, unavailable_repos_filepath, "Unavailable repositories:"
    )

    return ok_repos
