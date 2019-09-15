from os import path

import config


class Singleton(object):  # 单例
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance


def plugin_dir(file):
    parent, now = path.split(file)
    if now == '__init__.py':
        now = path.split(parent)[-1]
    else:
        now = now[:-3]
    return path.join(config.PLUGIN_DIR, now)
