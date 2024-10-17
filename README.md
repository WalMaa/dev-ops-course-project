# dev-ops-course-project

Fun little course project to mine software repositories and to conduct analysis on the refactoring done on them.

## Instructions

[RefactoringMiner](https://github.com/tsantalis/RefactoringMiner?tab=readme-ov-file#general-info) is mandatory for the application to work. Install it and make sure the binary can be called with the command RefactoringMiner (eg. you could create a symlink in /usr/local/bin to point to the RefactoringMiner executable)

Provide the following paths in _config.ini_:

```ini
[files]
csv_file =

[paths]
cloned_repositories_dir =
refactoring_results_dir =
refactoring_type_results_dir =
```

The directories should be empty before using the app.

The app will first read the source csv to extract github URL's. Lists of OK (status 200) and Not OK (other statuses) are created in the _results_ directory. The app will use the OK urls to clone the repositories to the _cloned_repositories_dir_ directory. Next, the app will run RefactoringMiner on the cloned repositories and place the resulting JSONs in the _refactoring_results_dir_ directory.
