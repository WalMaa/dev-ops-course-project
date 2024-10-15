import pandas as pd


df = pd.read_csv("sonar_measures.csv", low_memory=False, dtype={7: str, 8: str})

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


def main():
    for url in github_urls:
        print(url)


if __name__ == "__main__":
    main()
