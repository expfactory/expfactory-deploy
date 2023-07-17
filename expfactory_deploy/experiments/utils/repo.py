import json
import os
import pathlib
import time

import git
import jsonschema
from django.conf import settings
from git.exc import GitError

"""
Given a repo, crawl its subdirectories and return paths to directories with valid config.json
"""


def find_valid_dirs(repo):
    with open(pathlib.Path(__file__).parent.joinpath("experiment_schema.json")) as fp:
        schema = json.load(fp)
    valid_dirs = []
    errors = []
    # switch to scandir if too slow
    for root, dir, files in os.walk(repo):
        if "config.json" not in files:
            continue

        if "config.json" in files and "index.html" in files:
            # expfactory2 - todo
            continue
        with open(os.path.join(root, "config.json")) as config_fp:
            config = json.load(config_fp)
            try:
                validate = jsonschema.validate(config, schema)
                valid_dirs.append(root)
            except jsonschema.exceptions.ValidationError as e:
                errors.append(e)
                print("invalid")
    return valid_dirs, errors


"""
Process experiments found by find_valid_dirs, make new ExperimentRepoObjects if need be.
"""


def find_new_experiments(search_dir=settings.REPO_DIR):
    from experiments.models import ExperimentRepo, RepoOrigin

    print(f"searching {search_dir}")
    valid_dirs, errors = find_valid_dirs(search_dir)
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
    return (created_repos, created_experiments, errors)


# find_valid_dirs('../expfactory-experiments')


def get_latest_commit(repo_location, sub_dir=None):
    repo = git.Repo(repo_location)
    return repo.head.commit
    '''
    if sub_dir is None:
        return repo.head.commit.hexsha
    else:
        commits = repo.git.log(path, pretty="format:%H").split('\n')
        return commits.split('\n')[0]
    '''

def commit_date(repo_location, commit=None):
    repo = git.Repo(repo_location)
    if commit is None:
        commit = repo.head.commit
    else:
        commit = repo.commit(commit)
    return time.asctime(time.gmtime(commit.committed_date))

def is_valid_commit(repo_location, commit):
    try:
        repo = git.Repo(repo_location)
        repo.commit(commit)
        return True
    except GitError as e:
        return False

def pull_origin(repo_location):
    repo = git.Repo(repo_location)
    repo.remotes.origin.pull()
