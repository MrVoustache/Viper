"""
This module adds function wrappers that allows to work on secret values that can be deleted after declaration.
"""


from typing import Callable, TypeVar, ParamSpec, Concatenate

__all__ = ["secret"]




P = ParamSpec("P")
R = TypeVar("R")
S = TypeVar("S")

def secret(secret : S) -> Callable[[Callable[Concatenate[S, P], R]], Callable[P, R]]:
    """
    Decorator that creates a fonction that holds a secret.
    (Do not use for security, you can still get access to the secret)
    Example:
    >>> secret = "Secret message"
    >>> @secret_arg(secret)
    ... def print_secret(s):
    ...     print(s)
    ... 
    >>> del secret
    >>> print_secret()
    'Secret message'
    """
    def inner_dec(f : Callable[Concatenate[S, P], R]) -> Callable[P, R]:
        from Viper.meta.utils import signature_def, signature_call
        from functools import update_wrapper
        import re

        sig = "vault = vault\n"

        sig_def, env = signature_def(f, init_env = {"old_target" : f, "vault" : secret})

        try:
            a, b = re.compile(r"\(\w+,? *").search(sig_def).span()
            sig_def = sig_def[:a + 1] + sig_def[b:]
        except:
            raise ValueError("Given function must have at least one argument")
        
        code = sig + sig_def
        
        code += "\n\t"

        code += "return old_target(vault, "

        sig_call = signature_call(f, decorate = False)

        try:
            a, b = re.compile(r"\w+,? *").search(sig_call).span()
            sig_call = sig_call[:a] + sig_call[b:]
        except:
            raise ValueError("Given function must have at least one argument")

        code += sig_call + ")"

        code += "\n"

        # print(code)

        exec(code, env)

        new_f = env[f.__name__]

        update_wrapper(new_f, f, ('__module__', '__name__', '__qualname__', '__doc__'))

        annotations = f.__annotations__.copy()

        new_f.__annotations__ = annotations

        return new_f
    
    return inner_dec


del TypeVar, ParamSpec