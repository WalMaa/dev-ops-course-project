import pandas as pd
import re
import asyncio
from aiohttp import ClientSession, ClientError, ClientTimeout
import os


def get_github_urls(filename):
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
                print(f"Found URL: {url}")
    else:
        print(
            "The source csv file does not contain expected headers 'project' and 'organization'"
        )

    return github_urls


async def get_http_statuses_for_urls(session, urls):
    tasks = [test_http_status(session, url) for url in urls]
    return await asyncio.gather(*tasks)


async def test_http_status(session, url):
    try:
        async with session.get(url, timeout=ClientTimeout(total=60)) as response:
            print(f"{url} {response.status}")
            return f"{url} {response.status}"

    except asyncio.TimeoutError:
        print(f"{url} caused timeout")
        return f"{url} 408"

    except ClientError as error:
        print(f"Request failed for {url}: {str(error)}")
        return f"{url} request failed"


def write_to_text_file(collection, filepath):
    with open(filepath, "a") as file:
        file.truncate(0)
        for item in collection:
            file.write(f"{item}{'\n'}")


def write_to_text_file_and_print(collection, filepath, header):
    with open(filepath, "a") as file:
        file.truncate(0)

        print(f"\n{header}")

        if len(collection) > 0:
            for item in collection:
                file.write(f"{item}\n")
                print(item)
        else:
            print("None!")


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
    print("Repository fetcher is running...")
    https_urls = get_github_urls(csv_file)
    ssh_urls = convert_https_to_ssh(https_urls)
    os.makedirs("results", exist_ok=True)
    os.makedirs("results/repo_lists", exist_ok=True)
    http_statuses = []
    ok_repos = []
    unavailable_repos = []

    write_to_text_file_and_print(
        ssh_urls, "results/repo_lists/ssh_urls.txt", "All repositories:"
    )

    # Test the http responses of the github urls, eg. 200, 301, 400
    async with ClientSession() as session:
        print("\nHTTP statuses of the repositories:")
        http_statuses = await get_http_statuses_for_urls(session, https_urls)

    write_to_text_file(http_statuses, "results/repo_lists/https_statuses.txt")

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
        "results/repo_lists/ok_repos.txt",
    )

    write_to_text_file_and_print(
        sorted(unavailable_repos, key=str.casefold),
        "results/repo_lists/unavailable_repos.txt",
        "Unavailable repositories:",
    )

    count_ok = len(ok_repos)
    count_unavailable = len(unavailable_repos)

    print(
        f"\nRepository fetcher is finished. Found {count_ok} OK repositories and {count_unavailable} unavailable repositories."
    )
