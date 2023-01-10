import argparse
import json
import os
import sys
import urllib
from pathlib import Path

from .utils import generate_experiment_context

import web
from web.contrib.template import render_jinja

urls = ("/(.*)/serve", "serve", "/(.*)/decline", "decline")
web.config.debug = False
app = web.application(urls, globals())
session = web.session.Session(
    app, web.session.DiskStore("sessions"), initializer={"incomplete": None}
)

parser = argparse.ArgumentParser(description="Start local deployment of battery")
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "exp_config",
    metavar="EXP_config",
    type=Path,
    help="configuration file to run experiments",
    nargs='?'
)

group.add_argument(
    '-e',
    '--exps',
    help="comma delimited list of paths to experiments",
    type=lambda x: [Path(y) for y in x.split(',')]
)

experiments = []
exp_location = ""
order = "random"
output_file = Path(os.getcwd(), "./results.txt")

package_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = ""
template_dir = Path(package_dir, "templates")
static_dir = Path(package_dir, "static/")
render = render_jinja(template_dir, encoding="utf-8")

def run(args=None):
    args = parser.parse_args(args)
    if (args.exps is not None):
        experiments = args.exps
    elif (args.exp_config is not None):
        if (args.exp_config.is_file()):
            with open(args.exp_config) as fp:
                experiments = [Path(x.strip()) for x in fp.readlines()]
        else:
            experiments=[args.exp_config]
    else:
        experiments=[os.getcwd()]

    for experiment in experiments:
        try:
            os.symlink(experiment, Path(static_dir, experiment.stem))
        except FileExistsError:
            os.unlink(Path(static_dir, experiment.stem))
            os.symlink(experiment, Path(static_dir, experiment.stem))

    web.config.update({'experiments': experiments})
    # I think directory with a period in dirname of sys.argv[0] threw run func for a loop.
    # We don't need argv anymore so can clear it.
    sys.argv = []
    app.run()

def serve_experiment(experiment):
    exp_name = experiment.stem
    context = generate_experiment_context(Path(static_dir, exp_name), "/", f"/static/{exp_name}")
    return render.deploy_template(**context)


class serve:
    def GET(self, name):
        experiments = web.config.experiments
        if session.get('incomplete') == None:
            session.incomplete = [*experiments]
        if len(session.incomplete) == 0:
            return render.finished()
        exp_to_serve = session.incomplete[-1]
        return serve_experiment(exp_to_serve)

    def POST(self, name):
        session.incomplete.pop()
        with open(Path(results_dir, output_file), "ab") as fp:
            data = web.data()
            fp.write(data)
        web.header("Content-Type", "application/json")
        return "{'success': true}"


class decline:
    def GET(self, name):
        app.stop()


if __name__ == "__main__":
    sys.argv = [sys.argv[1]]
    run(args=sys.argv)
