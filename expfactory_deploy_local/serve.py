import argparse
import json
import os
import sys
import urllib
from pathlib import Path

import web
from web.contrib.template import render_jinja

urls = ("/(.*)/serve", "serve", "/(.*)/decline", "decline")
web.config.debug = False
app = web.application(urls, globals())
session = web.session.Session(
    app, web.session.DiskStore("sessions"), initializer={"incomplete": None}
)

parser = argparse.ArgumentParser(description="Start local deployment of battery")
parser.add_argument(
    "exp_config",
    metavar="EXP_config",
    type=Path,
    nargs=1,
    help="configuration file to run experiments",
)
args = parser.parse_args()

experiments = []
exp_location = ""
order = "random"
output_file = Path("./results.txt")
results_dir = ""
template_dir = "templates"
render = render_jinja(template_dir, encoding="utf-8")

with open(args.exp_config[0]) as fp:
    experiments = [Path(x.strip()) for x in fp.readlines()]

for experiment in experiments:
    try:
        os.symlink(experiment, Path("./static/", experiment.stem))
    except FileExistsError:
        os.unlink(Path("./static/", experiment.stem))
        os.symlink(experiment, Path("./static/", experiment.stem))


def serve_experiment(experiment):
    exp_name = experiment.stem
    context = generate_experiment_context(exp_name, "/static")
    return render.deploy_template(**context)


class serve:
    def GET(self, name):
        print(session.incomplete)
        if session.incomplete == None:
            session.incomplete = [*experiments]
            print(experiments)
            print([*experiments])
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
    sys.argv = [sys.argv[0]]
    app.run()
