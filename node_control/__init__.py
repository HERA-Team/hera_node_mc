from pkg_resources import get_distribution, DistributionNotFound
from setuptools_scm import get_version
from pathlib import Path

from . import node_control
from . import send_receive
from . import node_util


try:  # This is used for developer installs
    __version__ = get_version(Path(__file__).parent.parent)
except (LookupError, ImportError):
    try:
        __version__ = get_distribution(__name__).version
    except DistributionNotFound:
        pass

__all__ = ['node_control', 'send_receive', 'node_util']
