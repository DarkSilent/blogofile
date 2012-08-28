# -*- coding: utf-8 -*-
"""Load the default config, and the user's _config.py file, and
provides the interface to the config.
"""

__author__ = "Ryan McGuire (ryan@enigmacurry.com)"

import os
import logging
import sys
import re
from . import cache
from . import controller
from . import plugin
# from . import site_init
from . import filter as _filter
from .cache import HierarchicalCache as HC
# TODO: This import MUST come after cache is imported; that's too brittle!
import blogofile_bf as bf


class ConfigNotFoundException(Exception):
    pass

logger = logging.getLogger("blogofile.config")

bf.config = sys.modules['blogofile.config']

site = cache.HierarchicalCache()
controllers = cache.HierarchicalCache()
filters = cache.HierarchicalCache()
plugins = cache.HierarchicalCache()
templates = cache.HierarchicalCache()

default_config_path = os.path.join(
    os.path.dirname(__file__), "default_config.py")


def init_interactive(args=None):
    """Reset the blogofile cache objects, and load the configuration.

    The user's _config.py is always loaded from the current directory
    because we assume that the function/method that calls this has
    already changed to the directory specified by the --src-dir
    command line option.
    """
    cache.reset_bf()
    try:
        _init("_config.py")
    except ConfigNotFoundException:
        sys.stderr.write("No configuration found in source dir: {0}\n"
                         .format(args.src_dir))
        sys.stderr.write("Want to make a new site? Try `blogofile init`\n")
        sys.exit(1)


def _init(config_file_path=None):
    """Initialize the configuration.

    If config_file_path is None, just load the default config
    """
    logger.info("Loading config file : {0}".format(config_file_path))
    if config_file_path:
        if not os.path.isfile(config_file_path):
            raise ConfigNotFoundException
        _load_config(config_file_path)
    else:
        _load_config()


def _load_config(user_config_path=None):
    """Load the configuration.

    Strategy:

      1) Load the default config
      2) Load the plugins
      3) Load the site filters and controllers
      4) Load the user's config.
      5) Compile file ignore pattern regular expressions

    This establishes sane defaults that the user can override as they
    wish.

    config is exec-ed from Python modules into locals(), then updated
    into globals().
    """
    with open(default_config_path) as f:
        exec(f.read())
    plugin.load_plugins()
    _filter.preload_filters()
    controller.load_controllers(namespace=bf.config.controllers)
    try:
        with open(user_config_path) as f:
            exec(f.read())
    except IOError:
        pass
    _compile_file_ignore_patterns()
    globals().update(locals())


def _compile_file_ignore_patterns():
    site.compiled_file_ignore_patterns = []
    for p in site.file_ignore_patterns:
        if hasattr(p, "findall"):
            # probably already a compiled regex.
            site.compiled_file_ignore_patterns.append(p)
        else:
            site.compiled_file_ignore_patterns.append(
                re.compile(p, re.IGNORECASE))
