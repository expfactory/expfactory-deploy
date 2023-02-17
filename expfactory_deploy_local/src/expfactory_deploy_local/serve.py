import argparse
import json
import os
import sys
import urllib
from pathlib import Path

from .utils import generate_experiment_context

import web
from web.contrib.template import render_jinja

package_dir = os.path.dirname(os.path.abspath(__file__))

urls = ("/", "serve", "/serve", "serve", "/decline", "decline")
web.config.debug = False
app = web.application(urls, globals())
session = web.session.Session(
    app, web.session.DiskStore(Path(package_dir, "sessions")), initializer={"incomplete": None }
)

parser = argparse.ArgumentParser(description="Start a local deployment of a battery")
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "exp_config",
    metavar="EXP_config",
    type=Path,
    help="Path to a single experiment or path to a configuration file. Configuration file should be a single path to an experiment per line.",
    nargs='?'
)
group.add_argument(
    '-e',
    '--exps',
    help="Comma delimited list of paths to experiments. Mutually exclusive with exp_config",
    type=lambda x: [Path(y) for y in x.split(',')]
)

experiments = []

output_file = Path(os.getcwd(), "./results.txt")
template_dir = Path(package_dir, "templates")
static_dir = Path(package_dir, "static/")
experiments_dir = Path(static_dir, "experiments/")
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
        print("Found arguments:")
        print(args)
        print()
        parser.print_help()
        sys.exit()

    dne = [print(f"{e.absolute()} Does not exist. Ignoring") for e in experiments if not e.exists()]
    experiments = [e.absolute() for e in experiments if e.exists()]

    if len(experiments) == 0:
        print("No Experiments Found")
        sys.exit()

    for experiment in experiments:
        try:
            os.symlink(experiment, Path(experiments_dir, experiment.stem))
        except FileExistsError:
            os.unlink(Path(experiments_dir, experiment.stem))
            os.symlink(experiment, Path(experiments_dir, experiment.stem))

    web.config.update({'experiments': experiments})
    # I think a directory starting with a period in the dirname of
    # sys.argv[0] threw webpy run func for a loop.
    # We don't need argv anymore so can clear it.
    sys.argv = []
    app.run()

def serve_experiment(experiment):
    exp_name = experiment.stem
    context = generate_experiment_context(Path(experiments_dir, exp_name), "/", f"/static/experiments/{exp_name}")
    return render.deploy_template(**context)


class serve:
    def GET(self):
        experiments = web.config.experiments
        if session.get('experiments') == None:
            session.experiments = [*experiments]
        if set(experiments) != set(session.experiments):
            session.experiments = [*experiments]
            session.incomplete = [*experiments]
        if session.get('incomplete') == None:
            session.incomplete = [*experiments]

        if len(session.incomplete) == 0:
            return render.finished()
        exp_to_serve = session.incomplete[-1]
        return serve_experiment(exp_to_serve)

    def POST(self):
        session.incomplete.pop()
        with open(output_file, "ab") as fp:
            data = web.data()
            fp.write(data)
        web.header("Content-Type", "application/json")
        return "{'success': true}"


class decline:
    def GET(self, name):
        app.stop()


if __name__ == "__main__":
    run()
