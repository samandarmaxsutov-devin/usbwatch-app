"""Tiny observable + command primitives so view-models never import Tkinter.

A View subscribes to an Observable and updates its widgets in the callback; it calls
Commands in response to user input. All notifications happen on whichever thread sets
the value, so view-models only mutate observables from the UI thread (the tick loop).
"""


class Observable:
    """Holds a value and notifies subscribers when it changes."""

    __slots__ = ("_value", "_subs")

    def __init__(self, value=None):
        self._value = value
        self._subs = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new):
        if new != self._value:
            self._value = new
            self._notify()

    def set(self, new):
        """Set and always notify, even if the value is equal (use for lists)."""
        self._value = new
        self._notify()

    def subscribe(self, callback, immediate=True):
        """Register callback(value); returns an unsubscribe function."""
        self._subs.append(callback)
        if immediate:
            callback(self._value)

        def off():
            try:
                self._subs.remove(callback)
            except ValueError:
                pass

        return off

    def _notify(self):
        for cb in list(self._subs):
            cb(self._value)


class Command:
    """A callable the view invokes; optional can_execute guard."""

    __slots__ = ("_execute", "_can")

    def __init__(self, execute, can_execute=None):
        self._execute = execute
        self._can = can_execute

    def can_execute(self, *args):
        return self._can is None or bool(self._can(*args))

    def __call__(self, *args, **kwargs):
        if self.can_execute(*args):
            return self._execute(*args, **kwargs)
        return None
