"""
This module defines a copy of you Python Interactive Interpreter.
"""

from typing import Any

__all__ = ["InteractiveInterpreter"]





class InteractiveInterpreter:

    """
    This is an interactive interpreter that will mimic the external interpreter.
    """

    def __init__(self, env : dict[str, Any] | None = None) -> None:
        if env is None:
            env = {}
        self.__env = env
    
    @property
    def env(self) -> dict[str, Any] | None:
        """
        The current environment used for this interpreter.
        """
        return self.__env

    @env.setter
    def env(self, value : dict[str, Any] | None):
        if value is not None and not isinstance(value, dict):
            raise TypeError("Expected None or dict, got " + repr(type(value).__name__))
        self.__env = value
    
    def interact(self, banner : str | None = None, exit_message : str | None = None):
        """
        Starts the interactive interpreter. Returns at interpreter exit.
        """

        if (banner is not None and not isinstance(banner, str)) or (exit_message is not None and not isinstance(exit_message, str)):
            raise TypeError("Expected str or None, str or None, got " + repr(type(banner).__name__) + " and " + repr(type(exit_message).__name__))

        import code
        import os
        import sys

        filename = os.environ.get('PYTHONSTARTUP')
        old_ps1 = sys.ps1 if hasattr(sys, "ps1") else None
        old_ps2 = sys.ps2 if hasattr(sys, "ps2") else None
        try:
            if filename:
                exec(open(filename, "r").read(), {})

            try:
                import readline
                import rlcompleter
                readline.set_completer(rlcompleter.Completer(self.__env).complete)
                readline.parse_and_bind("tab: complete")
            except ModuleNotFoundError:
                pass
            code.InteractiveConsole(self.__env, "<InteractiveInterpreter at #{}>".format(hex(id(self)))).interact(banner, exit_message)
        finally:
            if old_ps1 is None and hasattr(sys, "ps1"):
                del sys.ps1
            else:
                sys.ps1 = old_ps1
            if old_ps1 is None and hasattr(sys, "ps2"):
                del sys.ps2
            else:
                sys.ps2 = old_ps2





del Any