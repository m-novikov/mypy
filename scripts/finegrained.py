"""Prototype for using fine-grained incremental checking interactively.

Usage:

- first start it
  $ finegrained.py <dir>
- it now waits for user input
  - an empty line performs an incremental step
  - 'q' exits
"""

import glob
import sys
import os
from typing import Tuple, List, Dict

from mypy import build
from mypy.build import BuildManager, Graph
from mypy.main import expand_dir
from mypy.options import Options
from mypy.errors import CompileError
from mypy.server.update import FineGrainedBuildManager


def main() -> None:
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        usage()
    target_dir = sys.argv[1]
    messages, manager, graph = build_dir(target_dir)
    for message in messages:
        sys.stdout.write(message + '\n')
    fine_grained_manager = FineGrainedBuildManager(manager, graph)
    ts = timestamps(target_dir)
    while True:
        inp = input('>>> ').strip()
        if inp.startswith('q'):
            sys.exit(0)
        if inp != '':
            print("Press enter to perform type checking; enter 'q' to quit")
            continue
        changed = None
        new_ts = timestamps(target_dir)
        for path in ts:
            if new_ts[path] != ts[path]:
                changed = path
                break
        ts = new_ts
        if not changed:
            print('[nothing changed]')
            continue
        print('[update {}]'.format(changed))
        messages = fine_grained_manager.update([changed])
        for message in messages:
            sys.stdout.write(message + '\n')


def build_dir(target_dir: str) -> Tuple[List[str], BuildManager, Graph]:
    sources = expand_dir(target_dir)
    options = Options()
    options.show_traceback = True
    options.cache_dir = os.devnull
    try:
        result = build.build(sources=sources,
                             options=options)
    except CompileError as e:
        # TODO: We need a manager and a graph in this case as well
        assert False, str('\n'.join(e.messages))
        return e.messages, None, None
    return result.errors, result.manager, result.graph


def timestamps(target_dir: str) -> Dict[str, float]:
    paths = glob.glob('%s/**/*.py' % target_dir) + glob.glob('%s/*.py' % target_dir)
    result = {}
    for path in paths:
        mod = path[:-3].replace('/', '.')
        result[mod] = os.stat(path).st_mtime
    return result


def usage() -> None:
    print('usage: finegrained.py DIRECTORY')
    sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except EOFError:
        print('^D')
