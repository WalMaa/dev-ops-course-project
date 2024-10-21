import asyncio
from datetime import timedelta, datetime
from aiohttp import ClientSession, ClientError
import json
import aiofiles
import os


async def count_commit_types(file):
    try:
        async with aiofiles.open(file, "r") as f:
            data = await f.read()
            data = json.loads(data)

            types = {}
            shas = []

            for commit in data["commits"]:
                repo_name = commit["repository"].replace("git@github.com:", "")

                for refactoring in commit.get("refactorings", []):
                    commit_type = refactoring.get("type")
                    if commit_type:
                        if commit_type in types:
                            types[commit_type] += 1
                        else:
                            types[commit_type] = 1

                sha = commit.get("sha1")
                if sha:
                    shas.append(sha)

            sorted_types = [
                {"type": commit_type, "count": count}
                for commit_type, count in sorted(
                    types.items(), key=lambda item: item[1], reverse=True
                )
            ]

            # print(f"\nFor repository {repo_name}, the following types were found:")
            # for entry in sorted_types:
            #     print(f"{entry["type"]}, {entry["count"]}")
            #
            # print("\nFollowing commit ID's were found:")
            # for id in shas:
            #     print(id)

            return {
                "repository": repo_name,
                "refactoring_types": sorted_types,
                "shas": shas,
            }

    except FileNotFoundError:
        print(f"Error: File {file} not found")
        return {}

    except json.JSONDecodeError:
        print(f"Error: File {file} is not valid JSON")
        return {}

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return {}


async def get_avg_inter_refactoring_times(
    session, github_apikey, commit_ids, repo_name
):
    urls = []

    for id in commit_ids:
        urls.append(f"https://api.github.com/repos/{repo_name}/commits/{id}")

    dates = await get_all_dates_for_repository(session, github_apikey, urls)

    # Convert to unix time ???
    return dates


async def get_all_dates_for_repository(session, github_apikey, urls):
    tasks = [get_date(session, github_apikey, url) for url in urls]
    return await asyncio.gather(*tasks)


async def get_date(session, github_apikey, url):
    headers = {
        "Authorization": f"Bearer {github_apikey}",
    }

    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                print(f"Got timestamp for {url}")
                data = await response.json()
                timestamp = data.get("commit").get("committer").get("date")
                if timestamp:
                    return timestamp
            elif response.status == 403:
                print(f"{url} returns 403, perhaps you exceeded your API limits?")
            else:
                print(
                    f"Could not get timestamp for {url}, response code: {response.status}"
                )

    except ClientError as error:
        print(f"Request failed for {url}: {str(error)}")


def calculate_avg_time_diff(times):
    time_differences = []
    datetime_objects = [datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ") for t in times]

    for index in range(len(datetime_objects) - 1):
        diff = (datetime_objects[index + 1] - datetime_objects[index]).total_seconds()
        time_differences.append(diff)

    avg = sum(time_differences) / len(time_differences)

    return timedelta(seconds=avg)


async def analyze(github_apikey):
    files = [
        (f.path, f.name)
        for f in os.scandir("results/miner_results")
        if f.is_file() and f.name.endswith(".json")
    ]

    os.makedirs("results", exist_ok=True)
    os.makedirs("results/part_c", exist_ok=True)

    async with ClientSession() as session:
        results = await asyncio.gather(*(count_commit_types(file[0]) for file in files))

        for repository in results:
            dates = await get_avg_inter_refactoring_times(
                session,
                github_apikey,
                repository.get("shas"),
                repository.get("repository"),
            )
            time_diff = calculate_avg_time_diff(dates)
            del repository["shas"]
            repository["avg_commit_time_diff"] = time_diff

        filename = "results/part_c/refactoring_type_results.json"

        with open(filename, "a") as file:
            file.truncate(0)
            json.dump(results, file)
