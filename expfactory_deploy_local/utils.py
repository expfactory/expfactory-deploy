""" Common functions used by webpy and django deployments """
from pathlib import Path

js_tag = "<script src={}></script>"
css_tag = '<link rel="stylesheet" type="text/css" href="{}">'
""" Poldrack lab expfactory-experiments/surveys config files have an array
    strings that are resources that need to be loaded for experiment to work.
    This function puts them in the appropriate html tags, and allows the
    location of the scripts to be adjusted depending on deployment.
"""


def format_external_scripts(scripts, exp_location, static_location="/"):
    print(scripts)
    print(exp_location)
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


def generate_experiment_context(experiment, static_location):
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
    with open(experiment / "config.json") as f:
        config = json.load(f)
        if isinstance(config, list):
            config = config[0]

    # should be renamed to external_scripts or something
    experiment_load = format_external_scripts(
        config["run"], Path(static_location, exp_name)
    )
    uniqueId = 0
    context = {
        "experiment_load": experiment_load,
        "uniqueId": uniqueId,
        "post_url": "./serve",
        "next_page": "./serve",
        "exp_id": exp_name,
        "exp_end": "./decline",
    }
    return context
