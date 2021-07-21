import argparse
import json
import os
import sys
import web

from pathlib import Path
from web.contrib.template import render_jinja

urls = (
    '/(.*)/serve', 'serve'
)
web.config.debug = False
app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore("sessions"), initializer={"incomplete": None})

parser = argparse.ArgumentParser(description='Start local deployment of battery')
parser.add_argument('exp_config', metavar='EXP_config', type=Path, nargs=1,
                    help='configuration file to run experiments')
args = parser.parse_args()

experiments = []
exp_location = ""
order = "random"
output_file = Path("./results.txt")
results_dir = ""
template_dir = "templates"
render = render_jinja(template_dir, encoding = 'utf-8')

with open(args.exp_config[0]) as fp:
    exps = fp.read()
    if isinstance(exps, list):
        exps = exps.striplines()
    else:
        exps = [exps.strip('\n')]
    experiments = [Path(x) for x in exps]

for experiment in experiments:
    try:
        os.symlink(experiment, Path('./static/', experiment.stem))
    except FileExistsError:
        os.unlink(Path('./static/', experiment.stem))
        os.symlink(experiment, Path('./static/', experiment.stem))


js_tag = '<script src={}></script>'
css_tag = '<link rel="stylesheet" type="text/css" href="{}">'
""" Poldrack lab expfactory-experiments/surveys config files have an array
    strings that are resources that need to be loaded for experiment to work.
    This function puts them in the appropriate html tags, and allows the
    location of the scripts to be adjusted depending on deployment.
"""
def format_external_scripts(scripts, exp_location, static_location='/'):
    js = []
    css = []
    for script in scripts:
        href = ""
        ext = script.split(".")[-1]

        if script.startswith('static'):
            href = Path(static_location, script)
        elif script.startswith('http') or script.startswith('/'):
            href = script
        else:
            href = Path(exp_location, script)

        if ext == "js":
            js.append(js_tag.format(href))
        elif ext == "css":
            css.append(css_tag.format(href))

    return "\n".join([*js, *css])

def serve_experiment(experiment):
    exp_name = experiment.stem
    config = {}
    with open( experiment / "config.json") as f:
        config = json.load(f)
        if isinstance(config, list):
            config = config[0]

    print(config)
    # should be renamed to external_scripts or something
    experiment_load = format_external_scripts(config['run'], Path('/static', exp_name ))
    uniqueId = 0
    context = {
        "experiment_load": experiment_load,
        "uniqueId": uniqueId,
        "post_url": "/sync/",
        "next_page": "/some_url",
        "exp_id": exp_name,
        "exp_end": "/some_url"
    }
    '''
    experiment_load - list of scripts
    uniqueId - put in trial data, used to signify real exp vs preview
    amazon_host assignment_id hit_id - do we actually need these for mturk?
    end_message - message displayed at end of experiment
    post_url - url to post experiment results to.
    next_page - page to go to if post successful
    exp_id -
    exp_end - url to tell server you're done/declined
    '''

    return render.deploy_template(**context)

class serve:
    def GET(self, name):
        if session.incomplete == None:
            session.incomplete = [*experiments]
        elif len(session.incomplete) == 0:
            app.stop()
        exp_to_serve = session.incomplete[-1]
        return serve_experiment(exp_to_serve)

    def POST(self, name):
        session.pop()
        with output_file.open(results_dir, 'a') as fp:
            f.write(web.data())
            f.write('\n')



if __name__ == "__main__":
    sys.argv = [sys.argv[0]]
    app.run()
