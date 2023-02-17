""" Common functions used by webpy and django deployments """
import json
from pathlib import Path

js_tag = '<script src="{}"></script>'
css_tag = '<link rel="stylesheet" type="text/css" href="{}">'
""" Poldrack lab expfactory-experiments/surveys config files have an array
    strings that are resources that need to be loaded for experiment to work.
    This function puts them in the appropriate html tags, and allows the
    location of the scripts to be adjusted depending on deployment.
"""


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


def generate_experiment_context(
    exp_fs_path, static_url_path='/', exp_url_path=None, static_rewrite=None, post_url="./serve", next_page="./serve"
):
    """context used in old template
    experiment_load - list of scripts
    uniqueId - put in trial data, used to signify real exp vs preview
    amazon_host assignment_id hit_id - do we actually need these for mturk?
    end_message - message displayed at end of experiment
    post_url - url to post experiment results to.
    next_page - page to go to if post successful
    exp_id -
    exp_end - url to tell server you're done/declined
    """

    config = {}
    with open(Path(exp_fs_path, "config.json")) as f:
        config = json.load(f)
        if isinstance(config, list):
            config = config[0]

    # we pass in an exp_location if filesystem pathing and url pathing differ
    if exp_url_path:
        experiment_load = format_external_scripts(
            config["run"], exp_url_path, static_url_path
        )
    else:
        experiment_load = format_external_scripts(
            config["run"], exp_fs_path, static_url_path
        )
    uniqueId = 0
    context = {
        "experiment_load": experiment_load,
        "uniqueId": uniqueId,
        "post_url": post_url,
        "next_page": next_page,
        "exp_id": exp_fs_path.stem,
        "exp_end": "./decline",
    }
    return context
