"""
Just some useful functions that solve metaclasses conflicts and that help generating exacutable Python code.
"""

from typing import Any, Callable

__all__ = ["signature_def", "signature_call", "merge"]





def signature_def(f : Callable, *, init_env : dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    """
    Creates a one line string that represents the definition line of the given function (with its complete signature) and an environment dict that allows you to execute this definition with type annotations and default values.
    """
    from inspect import signature, Parameter, _empty, isfunction

    if not isinstance(f, (staticmethod, classmethod)) and not isfunction(f):
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

def signature_call(f : Callable, param_arg_mapping : dict[str, str | None] | None = None, *, decorate : bool = True) -> str:
    """
    Creates a one line string that represents a call to given function (with its complete signature) that allows you to execute this function call.
    If given, param_arg_mapping should be a mapping from parameter names to argument names.
    In this dict, an argument name can be left to None, indicating that the default value should be used.
    If not given, the argument names will be the parameter names, and all will be used.
    If decorate is False, the name of the function and prentheses won't be added at the beginning of the string.
    """
    from inspect import signature, Parameter, _empty, isfunction

    if (not isinstance(f, (staticmethod, classmethod)) and not isfunction(f)) or (param_arg_mapping != None and not isinstance(param_arg_mapping, dict)):
        raise TypeError("Expected function and mapping or None, got " + repr(type(f).__name__) + " and " + repr(type(param_arg_mapping).__name__))
    if not isinstance(decorate, bool):
        raise TypeError("Expected bool for with_name, got " + repr(type(decorate).__name__))
    sig = signature(f)
    if param_arg_mapping == None:
        param_arg_mapping = {pname : pname for pname in sig.parameters}
    for param, param in param_arg_mapping.items():
        if not isinstance(param, str) or not isinstance(param, (str, type(None))):
            raise TypeError("param_arg_mapping sould be a str to str or None dict, got a " + repr((type(param), type(param))) + " pair")
    
    if decorate:
        call = f.__name__ + "("
    else:
        call = ""
    
    arguments = [[], [], [], [], []]
    for pname, param in sig.parameters.items():
        if pname in param_arg_mapping:
            aname = param_arg_mapping[pname]
            if param.kind == param.POSITIONAL_ONLY:
                arguments[0].append(aname)
            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                arguments[1].append(aname)
            elif param.kind == param.VAR_POSITIONAL:
                arguments[2].append("*" + aname)
            elif param.kind == param.KEYWORD_ONLY:
                arguments[3].append(pname + "=" + aname)
            elif param.kind == param.VAR_KEYWORD:
                arguments[4].append("**" + aname)
        else:
            if param.default == _empty and param.kind not in (param.VAR_KEYWORD, param.VAR_POSITIONAL):
                raise SyntaxError("Missing non-default parameter : " + repr(pname))
    
    i = 0
    while i < len(arguments):
        if not arguments[i]:
            arguments.pop(i)
        else:
            i += 1
    
    call += ", ".join(", ".join(argij for argij in argi) for argi in arguments)
    
    if decorate:
        call += ")"

    return call



def merge(*types : type) -> type:

    """
    Generates a class that inherits all of the given classes in order.
    """

    for t in types:
        if not issubclass(t, type):
            raise TypeError("Expected classes, got " + repr(type(t).__name__))

    class Mix(*types):
        pass

    return Mix

    



del Any, Callable