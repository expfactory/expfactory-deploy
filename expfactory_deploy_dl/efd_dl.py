# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
# ]
# ///
from enum import Enum
from typing import Optional, Annotated
from pathlib import Path

import csv
import json
import os
import platform
import subprocess

import typer

app = typer.Typer(no_args_is_help=True)

CONFIG_DIR = Path.home() / ".config" / "efd-dl"
CONFIG_FILE = CONFIG_DIR / "config.toml"

class ConfigKey(str, Enum):
    DEFAULT_TARGET = "default_target"
    DEFAULT_SOURCE = "default_source"
    KEY = "key"

CONFIG_KEY_DESCRIPTIONS = {
    ConfigKey.DEFAULT_TARGET: "Local directory where downloaded data will be stored",
    ConfigKey.DEFAULT_SOURCE: "Remote server URL and path (e.g., user@server.com:~/path/)",
    ConfigKey.KEY: "Path to SSH private key file for server authentication"
}

REQUIRED_CONFIG_KEYS = [key.value for key in ConfigKey]

SSH_OPT = 'ssh -i {key}'
if platform.system == "Linux":
    SSH_OPT = '"ssh -i {key}"'



def load_config():
    if not CONFIG_FILE.exists():
        return {}

    try:
        import tomllib
        with open(CONFIG_FILE, 'rb') as f:
            return tomllib.load(f)
    except ImportError:
        typer.echo("Error: Python 3.11+ required for tomllib", err=True)
        return {}
    except Exception as e:
        typer.echo(f"Error reading config: {e}", err=True)
        return {}

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    toml_content = ""
    for key, value in config.items():
        # Escape quotes in values
        escaped_value = str(value).replace('"', '\\"')
        toml_content += f'{key} = "{escaped_value}"\n'

    with open(CONFIG_FILE, 'w') as f:
        f.write(toml_content)

def ensure_config():
    config = load_config()
    needs_save = False

    for key in ConfigKey:
        if key.value not in config or not config[key.value]:
            config[key.value] = typer.prompt(f"Please set {key.value} - {CONFIG_KEY_DESCRIPTIONS[key]}")
            if key is ConfigKey.DEFAULT_TARGET:
                config[key.value] = str(Path(config[key.value]).expanduser().resolve())
            needs_save = True

    if needs_save:
        save_config(config)
        typer.echo(f"Configuration saved to {CONFIG_FILE}")

    return config

@app.command(no_args_is_help=True)
def show():
    """Show current configuration values."""
    config = load_config()
    typer.echo("Current configuration:")
    for key in REQUIRED_CONFIG_KEYS:
        current_value = config.get(key, "<not set>")
        typer.echo(f"  {key}: {current_value}")
    typer.echo(f"\nConfiguration file: {CONFIG_FILE}")

@app.command(no_args_is_help=True)
def set(
    key: Annotated[ConfigKey, typer.Argument(help="Configuration key to set")],
    value: Annotated[str, typer.Argument(help="Value to set")]
):
    """Set a configuration value.

    Available configuration keys:
    • default_target: Local directory where downloaded data will be stored
    • default_source: Remote server URL and path (e.g., user@server.com:~/path/)
    • key: Path to SSH private key file for server authentication
    """
    config = load_config()
    config[key.value] = value
    save_config(config)
    typer.echo(f"Set {key.value} = {value}")

def rsync(target: str, id: Optional[int]=None, filters: Optional[list[str]]=None, config=None):
    if config is None:
        config = load_config()
    default_source = config['default_source']
    key = config['key']

    source = default_source
    if id:
        # Extract base URL from default_source
        base_url = default_source.split(':')[0]
        source = f"{base_url}:~/results_export/battery-{id}"

    command = [ "rsync", "-avmP", "-e" ]
    command.extend(SSH_OPT.format(key=key)

    if filters:
        command.extend('--include="*/"'),
        command.extend([f'--include="{x}"' for x in filters])
        command.extend('--exclude="*"')

    command.extend([source, target])

    subprocess.run(' '.join(command), shell=True, check=True)

def target_validation(target: str):
    target_path = Path(target).expanduser().resolve()
    if target_path.is_dir():
        return target
    if target_path.is_file():
        raise typer.BadParameter("Target is a file not a directory.")

    target_path.mkdir(parents=True, exist_ok=True)
    print(f'Directory {target_path} created.')
    return target

def xref_sc_ids(scs: list[str], target: str, filters: Optional[list[str]]=None, config=None):
    if config is None:
        config = load_config()
    default_source = config['default_source']
    key = config['key']

    sc_ids = [int(x.split('-')[1]) for x in scs]
    base_url = default_source.split(':')[0]
    command = [
        "rsync",
        "-avP",
        "-e",
        SSH_OPT.format(key=key),
        f"{base_url}:~/results_export/study_collections.json",
        target
    ]
    subprocess.run(command, check=True, shell=True)
    sc_meta = {}
    with open(Path(target).expanduser() / "study_collections.json", 'r') as fp:
        sc_meta = json.load(fp)
    sc_meta = [x for x in sc_meta if x['id'] in sc_ids]

    for sc in sc_meta:
        sc_target = Path(target) / sc['id']
        for study in sc["studies"]:
            id = study["battery"]
            rsync(sc_target, id, filters, config)

def parse_ids(ids: list[str]):
    by_type = {
        "battery_ids": [],
        "battery": [],
        "sub": [],
        "sc": [],
        "task": []
    }
    for id in ids:
        try:
            by_type["battery_ids"].append(int(id))
            continue
        except ValueError:
            pass

        ent = id.split('-')[0]
        try:
            by_type[ent].append(id)
        except KeyError:
            print(f"Invalid id: `{id}` ignoring...")
    return by_type

def build_filters(by_type: str):
    filters = []
    for k, v in by_type.items():
        if len(v) == 0:
            continue
        if len(filters) == 0:
            prefix = '*' if k != 'sub' else ''
            for elem in v:
                filters.append(f"{prefix}{elem}")
        else:
            for elem in v:
                for i, filter in enumerate(filters):
                    filters[i] = f"{filter}*{elem}"
    for i, filter in enumerate(filters):
        filters[i] = f"{filter}*"

    return filters

def filter_unified(target: str, config):
    dl_fnames = []
    for root, _, files in os.walk(target):
        for file in files:
            dl_fnames.append(file)
    command = [
        "rsync",
        "-avP",
        "-e",
        SSH_OPT.format(key=key),
        f"{base_url}:~/results_export/unified.csv",
        target
    ]
    subprocess.run(command, check=True, shell=True)
    with open(Path(target).expanduser() / "unified.csv", 'r') as fp:
        reader = csv.reader(fp)
    header = next(reader)
    unified = [x for x in reader if x[-1] in dl_fnames]

    with open(Path(target).expanduser() / "unified.csv", 'w') as fp:
        writer = csv.writer(fp)
        writer.writerows([*header, *unified])
    return

ids_help = """
Numbers with no entity are assumed to be batteries.

sc-<int> values Will download that study-collection's batteries into its own directory.

sub-<str> task-<str> and battery-<int> will act as filters, attempting to download all
files that match any combination of subject, task, and battery.

Multiples of any of these types may be included.

Ordering is not important.
"""
target_help = "Directory to download results to."

@app.command(no_args_is_help=True)
def dl(
    ids: Annotated[list[str], typer.Argument(help=ids_help)],
    target: Annotated[Optional[str], typer.Option(help=target_help)]=None,
):
    """ Download Results

    On first run you will prompted for default download location, ssh key location, and url for the server.
    """
    config = ensure_config()

    if target is None:
        target = config['default_target']
    target = target_validation(target)

    by_type = parse_ids(ids)
    battery_ids = by_type.pop("battery_ids")
    scs = by_type.pop("sc")
    filters = build_filters(by_type)

    if battery_ids:
        for id in battery_ids:
            rsync(target, id, filters, config)
    if scs:
        xref_sc_ids(scs, target, filters, config)
    if not battery_ids and not scs and filters:
        rsync(target, filters=filters, config=config)
    filter_unified(target, config)
    return

def main():
    app()

if __name__ == "__main__":
    main()
