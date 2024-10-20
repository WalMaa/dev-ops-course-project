import asyncio
import json
import aiofiles
import os


async def count_commit_types(file):
    try:
        async with aiofiles.open(file, "r") as f:
            data = await f.read()
            data = json.loads(data)

            types = {}

            for commit in data["commits"]:
                repo_name = commit["repository"].replace("git@github.com:apache/", "")

                for refactoring in commit.get("refactorings", []):
                    commit_type = refactoring.get("type")
                    if commit_type:
                        if commit_type in types:
                            types[commit_type] += 1
                        else:
                            types[commit_type] = 1

            sorted_types = [
                {"type": commit_type, "count": count}
                for commit_type, count in sorted(
                    types.items(), key=lambda item: item[1], reverse=True
                )
            ]

            print(sorted_types)

            print(f"\nFor repository {repo_name}, the following types were found:")
            for entry in sorted_types:
                print(f"{entry["type"]}, {entry["count"]}")

            return {"repository": repo_name, "refactoring_types": sorted_types}

    except FileNotFoundError:
        print(f"Error: File {file} not found")
        return {}

    except json.JSONDecodeError:
        print(f"Error: File {file} is not valid JSON")
        return {}

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return {}


async def analyze():
    # TODO: Calculate the avg time between commits

    files = [
        (f.path, f.name)
        for f in os.scandir("results/miner_results")
        if f.is_file() and f.name.endswith(".json")
    ]

    os.makedirs("results", exist_ok=True)
    os.makedirs("results/part_c", exist_ok=True)

    results = await asyncio.gather(*(count_commit_types(file[0]) for file in files))
    filename = "results/part_c/refactoring_type_results.json"

    with open(filename, "a") as file:
        file.truncate(0)
        json.dump(results, file)
