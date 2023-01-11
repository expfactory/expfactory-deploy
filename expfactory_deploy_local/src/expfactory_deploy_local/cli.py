import sys
import os
from pathlib import Path
from contextlib import contextmanager
from .serve import static_dir, run

@contextmanager
def tempsymlink():
    local_static = Path(os.getcwd(), 'static/')
    if not local_static == static_dir:
        try:
            os.symlink(static_dir, local_static)
        except FileExistsError:
            os.unlink(local_static)
            os.symlink(static_dir, local_static)

    try:
        yield
    finally:
        try:
            if Path.is_symlink(local_static):
                os.unlink(local_static)
        except IOError:
            sys.stderr.write(f"Failed to unlink temporary symlink to static.")

def main():
    with tempsymlink() as _:
        run()
