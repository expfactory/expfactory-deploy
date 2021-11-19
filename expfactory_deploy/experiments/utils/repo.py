import json
import os
import pathlib

import git
import jsonschema
from django.conf import settings
from git.exc import GitError

"""
Given a repo, crawl its subdirectories and return paths to directories with valid config.json
"""


def find_valid_dirs(repo):
    fp = open(pathlib.Path(__file__).parent.joinpath("experiment_schema.json"))
    schema = json.load(fp)
    valid_dirs = []
    for root, dir, files in os.walk(repo):
        if "config.json" not in files:
            continue
        with open(os.path.join(root, "config.json")) as config_fp:
            config = json.load(config_fp)
            try:
                validate = jsonschema.validate(config, schema)
                valid_dirs.append(root)
            except jsonschema.exceptions.ValidationError:
                print("invalid")
    return valid_dirs


"""
Process experiments found by find_valid_dirs, make new ExperimentRepoObjects if need be.
"""


def find_new_experiments(search_dir=settings.REPO_DIR):
    from experiments.models import ExperimentRepo, RepoOrigin

    print(f"searching {search_dir}")
    valid_dirs = find_valid_dirs(search_dir)
    created_repos = []
    created_experiments = []
    for dir in valid_dirs:
        print(f"found valid_dir {dir}")
        repo = git.Repo(dir, search_parent_directories=True)
        repo_path = repo.git.rev_parse("--show-toplevel")
        repo_origin, repo_created = RepoOrigin.objects.get_or_create(
            origin=repo.remotes.origin.url, path=repo_path
        )
        experiment, experiment_created = ExperimentRepo.objects.get_or_create(
            name=os.path.split(dir)[-1], origin=repo_origin, location=dir
        )

        if repo_created:
            created_repos.append(repo_origin)
        if experiment_created:
            print(f"created new experiment entry")
            created_experiments.append(experiment)
    return (created_repos, created_experiments)


# find_valid_dirs('../expfactory-experiments')


def get_latest_commit(repo_location):
    repo = git.Repo(repo_location)
    return repo.head.commit.hexsha


def is_valid_commit(repo_location, commit):
    try:
        repo = git.Repo(repo_location)
        repo.commit(commit)
        return True
    except GitError as e:
        return False
