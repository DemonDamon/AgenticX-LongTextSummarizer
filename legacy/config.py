# Date    : 2024/9/26 22:31
# File    : config.py
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
