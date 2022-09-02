"""
Just some useful functions that help generating exacutable Python code.
"""

from typing import Any, Callable

__all__ = ["signature_str"]





def signature_str(f : Callable, *, init_env : dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    """
    Creates a one line string that represents the definition line of the given function (with its complete signature) and an environment dict that allows you to execute this definition with type annotations and default values.
    """
    from inspect import signature, Parameter, _empty, isfunction
    from typing import Any

    if not isfunction(f):
        raise TypeError("Expected function, got " + repr(type(f).__name__))
    if init_env == None:
        init_env = {}
    if not isinstance(init_env, dict):
        raise TypeError("Expected dict for init_env, got " + repr(type(init_env).__name__))

    def find_name(prefix : str) -> str:
        if prefix not in init_env:
            return prefix
        else:
            i = 1
            while prefix + "_" + str(i) in init_env:
                i += 1
            return prefix + "_" + str(i)

    sig = signature(f)

    abstract_sig = "def " + f.__name__ + "("

    arg_levels = {
        Parameter.POSITIONAL_ONLY : 0,
        Parameter.POSITIONAL_OR_KEYWORD : 1,
        Parameter.VAR_POSITIONAL : 2,
        Parameter.KEYWORD_ONLY : 3,
        Parameter.VAR_KEYWORD : 4
    }
    arg_numbers = [0, 0, 0, 0, 0]
    arg_level = 0

    done = False

    for i, (pname, param) in enumerate(sig.parameters.items()):
        if arg_level != arg_levels[param.kind]:
            if arg_levels[param.kind] > arg_levels[Parameter.POSITIONAL_ONLY] and arg_numbers[Parameter.POSITIONAL_ONLY] and not done:
                abstract_sig += "/, "
                done = True
            if param.kind == Parameter.KEYWORD_ONLY and arg_numbers[Parameter.VAR_POSITIONAL] == 0:
                abstract_sig += "*, "
            arg_level = arg_levels[param.kind]
        arg_numbers[arg_level] += 1
        if param.kind == Parameter.VAR_POSITIONAL:
            abstract_sig += "*"
        if param.kind == Parameter.VAR_KEYWORD:
            abstract_sig += "**"
        abstract_sig += pname

        if param.annotation != _empty:
            type_var = find_name("type_" + pname)
            init_env[type_var] = param.annotation
            abstract_sig += " : " + type_var
        if param.default != _empty:
            default_var = find_name("default_" + pname)
            init_env[default_var] = param.default
            abstract_sig += " = " + default_var
        if i + 1 < len(sig.parameters):
            abstract_sig += ", "
    
    abstract_sig += ")"

    if sig.return_annotation != _empty:
        return_var = find_name("return_type")
        init_env[return_var] = sig.return_annotation
        abstract_sig += " -> " + return_var
    
    abstract_sig += ":\n"

    return abstract_sig, init_env



del Any, Callable