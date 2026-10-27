"""Common base for page view-models."""
from ..core import Command, Observable

__all__ = ["ViewModel", "Observable", "Command"]


class ViewModel:
    """A page view-model holds a reference to the shell (shared services + state)."""

    def __init__(self, shell):
        self.shell = shell

    # convenience shortcuts
    @property
    def repo(self):
        return self.shell.repo

    @property
    def mon(self):
        return self.shell.mon

    @property
    def cfg(self):
        return self.shell.cfg
