import asyncio
import pandas as pd
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

            sorted_types = sorted(types.items(), key=lambda item: item[1], reverse=True)

            print(f"\nFor repository {repo_name}, the following types were found:")
            for commit_type, count in sorted_types:
                print(f"{commit_type}: {count}")

            return {repo_name: sorted_types}

    except FileNotFoundError:
        print(f"Error: File {file} not found")
        return {}

    except json.JSONDecodeError:
        print(f"Error: File {file} is not valid JSON")
        return {}

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return {}


async def analyze(src_dir, dest_dir):
    # TODO: Better output format
    # TODO: Calculate the avg time between commits

    files = [
        (f.path, f.name)
        for f in os.scandir(src_dir)
        if f.is_file() and f.name.endswith(".json")
    ]
    results = await asyncio.gather(*(count_commit_types(file[0]) for file in files))
    df = pd.DataFrame(results)

    flattened_results = []
    for result in results:
        if result:
            for repo_name, types in result.items():
                for commit_type, count in types:
                    flattened_results.append(
                        {"repository": repo_name, "type": commit_type, "count": count}
                    )

    filename = f"{dest_dir}/refactoring_type_results.txt"
    df = pd.DataFrame(flattened_results)
    df.to_csv(filename, sep="\t", index=False)
