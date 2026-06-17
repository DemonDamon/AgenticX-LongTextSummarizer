# Date    : 2024/9/26 22:35
# File    : utils.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


import os
import yaml
from types import SimpleNamespace


def _dict_to_namespace(d):
    """将字典转换为SimpleNamespace对象"""
    if isinstance(d, dict):
        for key, value in d.items():
            d[key] = _dict_to_namespace(value)
        return SimpleNamespace(**d)
    elif isinstance(d, list):
        return [_dict_to_namespace(item) for item in d]
    else:
        return d


def load_config(cpth):
    """加载配置文件"""
    assert os.path.exists(cpth), "配置文件不存在"
    with open(cpth, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    return _dict_to_namespace(config_dict)


def colorstr(*input, color="blue", bold=False, underline=False):
    colors = {'black': '\033[30m',  # basic colors
              'red': '\033[31m',
              'green': '\033[32m',
              'yellow': '\033[33m',
              'blue': '\033[34m',
              'magenta': '\033[35m',
              'cyan': '\033[36m',
              'white': '\033[37m',
              'orange': '\033[38;5;202m',
              'end': '\033[0m',  # misc
              'bold': '\033[1m',
              'underline': '\033[4m'}
    prefix = colors[color]
    if bold:
        prefix += colors["bold"]
    if underline:
        prefix += colors["underline"]

    return "{}{}{}".format(prefix, input[0], colors["end"])


def print_logo():
    logo = """
██████╗ ██╗ ██████╗██╗  ██╗██╗███╗   ██╗███████╗ ██████╗      █████╗ ██╗██████╗  ██████╗ ██╗  ██╗
██╔══██╗██║██╔════╝██║  ██║██║████╗  ██║██╔════╝██╔═══██╗    ██╔══██╗██║██╔══██╗██╔═══██╗╚██╗██╔╝
██████╔╝██║██║     ███████║██║██╔██╗ ██║█████╗  ██║   ██║    ███████║██║██████╔╝██║   ██║ ╚███╔╝
██╔══██╗██║██║     ██╔══██║██║██║╚██╗██║██╔══╝  ██║   ██║    ██╔══██║██║██╔══██╗██║   ██║ ██╔██╗
██║  ██║██║╚██████╗██║  ██║██║██║ ╚████║██║     ╚██████╔╝    ██║  ██║██║██████╔╝╚██████╔╝██╔╝ ██╗
╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝     ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝
"""
    print(colorstr(logo, color="orange"))