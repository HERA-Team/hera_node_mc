import contextlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from setuptools_scm import get_version

try:  # This is used for developer installs
    __version__ = get_version(Path(__file__).parent.parent)
except (LookupError, ImportError):
    with contextlib.suppress(PackageNotFoundError):
        __version__ = version(__name__)

from . import node_control
from . import send_receive
from . import node_util

__all__ = ['node_control', 'send_receive', 'node_util']
