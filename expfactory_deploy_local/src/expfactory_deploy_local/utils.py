""" Common functions used by webpy and django deployments """
import csv
import json
from pathlib import Path

def load_survey_tsv(path):
    lines = []
    with open(path) as f:
        tsv_file = csv.reader(f, delimiter="\t")
        for line in tsv_file:
            lines.append(line)

    questions = []
    for line in lines[1:]:
        row = {}
        if (len(line) < 2):
            continue
        for idx, header in enumerate(lines[0]):
            if (idx < len(line)):
                row[header] = line[idx]
            else:
                row[header] = ""

        questions.append(row)
    return questions

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
    context = {
        "js_vars": {}
    }
    with open(Path(exp_fs_path, "config.json")) as f:
        config = json.load(f)
        if isinstance(config, list):
            config = config[0]

    if config["template"] == "survey":
        config["run"].append("static/jspsych7/jspsych.js")
        config["run"].append("static/jspsych7/jspsych.css")
        config["run"].append("static/jspsych7/plugin-survey.js")
        config["run"].append("https://unpkg.com/@jspsych/plugin-survey@0.2.1/css/survey.css")
        config["run"].append("static/js/efSurvey.js")
        context["js_vars"]["_survey"] = load_survey_tsv(Path(exp_fs_path, "survey.tsv"))

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
    context.update({
        "experiment_load": experiment_load,
        "uniqueId": uniqueId,
        "post_url": post_url,
        "next_page": next_page,
        "exp_id": exp_fs_path.stem,
        "exp_end": "./decline",
    })

    return context
