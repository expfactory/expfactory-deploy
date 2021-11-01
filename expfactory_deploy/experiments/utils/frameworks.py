from pathlib import Path

import git
from django.conf import settings
from experiments import models as models

js_tag = '<script src="{}"></script>'
css_tag = '<link rel="stylesheet" type="text/css" href="{}">'


def format_external_scripts(scripts, exp_location, static_location="/"):
    js = []
    css = []
    for script in scripts:
        href = ""
        ext = script.split(".")[-1]

        if script.startswith("static"):
            href = Path(static_location, script)
        elif script.startswith("http") or script.startswith("/"):
            href = script
        else:
            href = Path(exp_location, script)

        if ext == "js":
            js.append(js_tag.format(href))
        elif ext == "css":
            css.append(css_tag.format(href))

    return "\n".join([*js, *css])


def get_context_data(experiment, exp_name):
    config = {}
    with open(experiment / "config.json") as f:
        config = json.load(f)
        if isinstance(config, list):
            config = config[0]

    print(config)
    # should be renamed to external_scripts or something
    experiment_load = format_external_scripts(config["run"], Path("/static", exp_name))
    uniqueId = 0
    context = {
        "experiment_load": experiment_load,
        "uniqueId": uniqueId,
        "post_url": "/sync/",
        "next_page": "/some_url",
        "exp_id": exp_name,
        "exp_end": "/some_url",
    }
    return context


def framework_dispatch(experiment, commit):
    name = experiment.name
    export_dir = Path(settings.EXPERIMENT_EXPORT_DIR, experiment, commit)
    repo = git.Repo(experiment.experiment_repo_id.location)
    repo_dir = repo.git.rev_parse("--show-toplevel")
    template = "classic.html"

    try:
        checkout = repo.execute(
            [
                "git",
                f"--work-tree={export_dir}",
                f"--git-dir={repo_dir}.git",
                "checkout" "-f",
                commit,
            ]
        )
    except Exception as e:
        # actually should catch git.exc.GitCommandError?
        print(e)

    get_context_data(export_dir)
    return (template, context)
