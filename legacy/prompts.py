# Date    : 2024/9/26 22:32
# File    : prompts.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


import yaml


def load_prompts():
    """加载提示词"""
    with open('prompts.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


_prompts = load_prompts()


def get_prompt(key):
    """获取指定的提示词"""
    return _prompts.get(key, '')


def format_prompt(key, **kwargs):
    """格式化提示词,类似于PromptTemplate的功能"""
    template = get_prompt(key)
    return template.format(**kwargs)