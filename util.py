from os import path

import config


def plugin_dir(file):
    parent, now = path.split(file)
    if now == '__init__.py':
        now = path.split(parent)[-1]
    else:
        now = now[:-3]
    return path.join(config.PLUGIN_DIR, now)
