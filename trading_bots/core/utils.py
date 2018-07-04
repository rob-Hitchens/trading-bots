import codecs
import importlib
import re

import yaml


def load_class_by_name(name: str):
    """Given a dotted path, returns the class"""
    mod_path, _, cls_name = name.rpartition('.')
    mod = importlib.import_module(mod_path)
    cls = getattr(mod, cls_name)
    return cls


def load_yaml_file(file_path: str):
    """Load a YAML file from path"""
    with codecs.open(file_path, 'r') as f:
        return yaml.safe_load(f)


def to_snake_case(name: str):
    """Converts a string to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
