import sys
from .repository import get_repo

_repo_impl = get_repo()

def __getattr__(name):
    return getattr(_repo_impl, name)
