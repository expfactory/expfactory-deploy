import argparse
import datetime
import json
import os
import sys
import urllib
from pathlib import Path

from .utils import generate_experiment_context

import web
from web.contrib.template import render_jinja

import polars as pl

web.config.debug = False

package_dir = os.path.dirname(os.path.abspath(__file__))

urls = ("/", "serve", "/serve", "serve", "/decline", "decline", "/reset", "reset")
app = web.application(urls, globals())
session = web.session.Session(
    app,
    web.session.DiskStore(Path(package_dir, "sessions")),
    initializer={"incomplete": None},
)


def create_parser():
    parser = argparse.ArgumentParser(
        description="Start a local deployment of a battery"
    )

    # Move exp_config into the mutually exclusive group AFTER creating it
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-e",
        "--exps",
        help="Comma delimited list of paths to experiments. Mutually exclusive with exp_config",
        type=lambda x: [Path(y) for y in x.split(",")],
    )
    group.add_argument(
        "-c",
        "--config",
        metavar="EXP_CONFIG",
        type=Path,
        help=(
            "Path to a single experiment or path to a configuration file. "
            "Configuration file should be a single path to an experiment per line."
        ),
    )

    # Additional arguments for BIDS formatting the output filename
    parser.add_argument(
        "-gi",
        "--group_index",
        help="Inject a group_index variable into the experiment context.",
    )
    parser.add_argument("-sub", "--subject_id", help="Subject ID")
    parser.add_argument("-ses", "--session_num", help="Session Number")
    parser.add_argument("-run", "--run_num", help="Run Number")

    # Output paths for BIDS and RAW data
    parser.add_argument("-raw", "--raw_dir", help="Path to raw data")
    parser.add_argument("-bids", "--bids_dir", help="Path to bids data")

    return parser


parser = create_parser()

experiments = []

template_dir = Path(package_dir, "templates")
static_dir = Path(package_dir, "static/")
experiments_dir = Path(static_dir, "experiments/")
render = render_jinja(template_dir, encoding="utf-8")


def rename_task(task_name):
    task_rename_mappings = {
        "ax_cpt_rdoc__fmri": "axCPT",
        "cued_task_switching_rdoc__fmri": "cuedTS",
        "flanker_rdoc__fmri": "flanker",
        "go_nogo_rdoc__fmri": "goNogo",
        "n_back_rdoc__fmri": "nBack",
        "operation_only_span_rdoc__fmri": "opOnlySpan",
        "operation_span_rdoc__fmri": "opSpan",
        "simple_span_rdoc__fmri": "simpleSpan",
        "spatial_cueing_rdoc__fmri": "spatialCueing",
        "spatial_task_switching_rdoc__fmri": "spatialTS",
        "stop_signal_rdoc__fmri": "stopSignal",
        "stroop_rdoc__fmri": "stroop",
        "visual_search_rdoc__fmri": "visualSearch",
    }
    return task_rename_mappings.get(task_name, task_name)


def create_events_file(data, bids_datafile):
    data = json.loads(data)
    trialdata = json.loads(data["trialdata"])

    flattened_data = []
    for trial in trialdata:
        flat_trial = {}
        for key, value in trial.items():
            if isinstance(value, (dict, list)):
                flat_trial[key] = json.dumps(value)
            else:
                flat_trial[key] = value
        flattened_data.append(flat_trial)

    df = pl.DataFrame(flattened_data)
    start_trial = df.filter(pl.col("trial_id") == "fmri_wait_block_trigger_start")
    start_trial_end = start_trial.select("time_elapsed").to_series()[0]

    # Create a mask that becomes True at fmri_wait_block_trigger_end and stays True thereafter
    mask = (pl.col("trial_id") == "fmri_wait_block_trigger_end").cum_max()
    events_df = df.filter(mask)
    events_df = events_df.with_columns(
        (pl.col("time_elapsed") - start_trial_end - pl.col("block_duration")).alias(
            "onset"
        )
    )

    events_df.write_csv(bids_datafile, separator="\t")
    print("Saved events datafile to: ", bids_datafile)
    return events_df


def run(args=None):
    args = parser.parse_args(args)
    if args.exps is not None:
        experiments = args.exps
    elif args.exp_config is not None:
        if args.exp_config.is_file():
            with open(args.exp_config) as fp:
                experiments = [Path(x.strip()) for x in fp.readlines()]
        else:
            experiments = [args.exp_config]
    else:
        print("Found arguments:")
        print(args)
        print()
        parser.print_help()
        sys.exit()

    experiments = [e.absolute() for e in experiments if e.exists()]

    if len(experiments) == 0:
        print("No Experiments Found")
        sys.exit()

    for experiment in experiments:
        try:
            os.mkdir(experiments_dir)
        except FileExistsError:
            pass
        try:
            os.symlink(experiment, Path(experiments_dir, experiment.stem))
        except FileExistsError:
            os.unlink(Path(experiments_dir, experiment.stem))
            os.symlink(experiment, Path(experiments_dir, experiment.stem))

    config_updates = {
        "experiments": experiments,
    }

    # Add params if not None
    optional_params = ["raw_dir", "bids_dir", "subject_id", "session_num", "run_num"]
    for param in optional_params:
        value = getattr(args, param)
        if value is not None:
            config_updates[param] = value

    web.config.update(config_updates)

    if args.group_index is not None:
        web.config.update({"group_index": args.group_index})

    sys.argv = []
    app.run()


def serve_experiment(experiment):
    exp_name = experiment.stem
    context = generate_experiment_context(
        Path(experiments_dir, exp_name), "/", f"/static/experiments/{exp_name}"
    )
    if web.config.get("group_index", None):
        context["group_index"] = web.config.group_index
    return render.deploy_template(**context)


class reset:
    def GET(self):
        session.kill()
        return '<html><body>Reset session, <a href="/">back to / </a></body></html>'


class serve:
    def GET(self):
        experiments = web.config.experiments
        if session.get("experiments") == None:
            session.experiments = [*experiments]
        if set(experiments) != set(session.experiments):
            session.experiments = [*experiments]
            session.incomplete = [*experiments]
        if session.get("incomplete") == None:
            session.incomplete = [*experiments]

        if len(session.incomplete) == 0:
            return render.finished()
        exp_to_serve = session.incomplete[-1]
        return serve_experiment(exp_to_serve)

    def POST(self):
        exp_name = session.incomplete.pop()
        date = str(int(datetime.datetime.now(datetime.timezone.utc).timestamp()))
        exp_name_stem = rename_task(exp_name.stem)

        raw_datafile = f"task-{exp_name_stem}_dateTime-{date}.json"
        bids_datafile = f"task-{exp_name_stem}.tsv"

        # Add bids naming conventions if provided
        if web.config.session_num:
            raw_datafile = f"ses-{web.config.session_num}_{raw_datafile}"
            bids_datafile = f"ses-{web.config.session_num}_{bids_datafile}"
        if web.config.subject_id:
            raw_datafile = f"sub-{web.config.subject_id}_{raw_datafile}"
            bids_datafile = f"sub-{web.config.subject_id}_{bids_datafile}"
        if web.config.run_num:
            raw_datafile = raw_datafile.replace(
                ".json", f"_run-{web.config.run_num}.json"
            )
            bids_datafile = bids_datafile.replace(
                ".tsv", f"_run-{web.config.run_num}.tsv"
            )

        if web.config.raw_dir:
            if web.config.subject_id:
                sub_dir = os.path.join(
                    web.config.raw_dir, f"sub-{web.config.subject_id}"
                )
                if web.config.session_num:
                    sub_ses_dir = os.path.join(
                        sub_dir, f"ses-{web.config.session_num}", "func"
                    )
                    os.makedirs(sub_ses_dir, exist_ok=True)
                    raw_datafile = os.path.join(sub_ses_dir, raw_datafile)
                else:
                    raw_datafile = os.path.join(sub_dir, raw_datafile)
            else:
                raw_datafile = os.path.join(web.config.raw_dir, raw_datafile)

        if web.config.bids_dir:
            if web.config.subject_id:
                sub_dir = os.path.join(
                    web.config.bids_dir, f"sub-{web.config.subject_id}"
                )
                if web.config.session_num:
                    sub_ses_dir = os.path.join(
                        sub_dir, f"ses-{web.config.session_num}", "func"
                    )
                    os.makedirs(sub_ses_dir, exist_ok=True)
                    bids_datafile = os.path.join(sub_ses_dir, bids_datafile)
                else:
                    bids_datafile = os.path.join(sub_dir, bids_datafile)
            else:
                bids_datafile = os.path.join(web.config.bids_dir, bids_datafile)

        with open(raw_datafile, "ab") as fp:
            data = web.data()
            fp.write(data)
            print("Saved raw datafile to: ", raw_datafile)

        web.header("Content-Type", "application/json")

        if "practice" not in exp_name_stem:
            create_events_file(web.data(), bids_datafile)

        return "{'success': true}"


class decline:
    def GET(self, name):
        app.stop()


if __name__ == "__main__":
    run()
