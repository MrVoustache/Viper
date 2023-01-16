"""
This module allows to precisely measure the execution time of one or multiple function during the execution of a program.
You can also generate execution reports.
This is made to improve the speed of your scripts.
"""


from numbers import Complex
from typing import Any, Callable, Dict, Iterable, List, Optional, ParamSpec, Tuple, TypeVar

__all__ = ["ExecutionInfo", "Chrono", "print_report"]





class ExecutionInfo:

    """
    A class that holds the information about a specific run of a function.
    """

    __slots__ = {
        "function" : "The function that was executed",
        "duration" : "The duration of the execution",
        "thread" : "The thread identifier of the thread that executed the function",
        "level" : "The call level that the function was called at"
    }

    def __init__(self) -> None:
        self.function = None
        self.duration = 0
        self.thread = 0
        self.level = 0

    
    def __str__(self) -> str:
        return "[Function {} lasted {} units of time in thread #{} at level {}]".format(self.function.__name__, self.duration, self.thread, self.level)




P = ParamSpec("P")
R = TypeVar("R")

class Chrono:

    """
    A chronometer class. Allows to measure execution time of multiple functions in a program (even at multiple levels).
    Can be used as a function decorator, timing every run of the function.

    A Chrono instance can take a custom clock function as argument. This should be a function with no arguments and should return a number.
    Careful : the default clock is process_time_ns (that measures CPU time for this process only). For example, using sleep won't make time pass.
    """

    def __init__(self, clock : Optional[Callable[[], Any]] = None) -> None:
        from typing import Dict, List, Tuple, Callable

        if clock == None:
            from time import process_time_ns
            clock = process_time_ns
        if not callable(clock):
            raise TypeError("Expected callable, got " + repr(clock.__class__.__name__))
        try:
            i = clock()
        except:
            raise ValueError("Clock function did not work")
        
        self.clock = clock
        self.__level : Dict[int, int] = {}
        self.__entries : List[Tuple[int, Callable, int, int, bool]] = []         # self.__entries[i] = (time, func, level, TID, in_or_out)
        self.__enabled : bool = True

    
    @property
    def enabled(self) -> bool:
        """
        True if this Chrono is enabled. If not, all timed function calls won't be measured.
        (It is made to reduce overhead when measures are not required.)
        """
        return self.__enabled
    

    @enabled.setter
    def enabled(self, value : bool):
        if not isinstance(value, bool):
            raise TypeError("Expected bool, got " + repr(type(value).__name__))
        self.__enabled = value

    
    def call(self, func : Callable[P, R], *args : Any, **kwargs : Any) -> R:
        """
        Calls function with given arguments and measures its execution time.
        Returns what the function returns.
        """
        if not self.enabled:
            return func(*args, **kwargs)

        from threading import get_ident
        TID = get_ident()
        if TID not in self.__level:
            self.__level[TID] = 0

        level = self.__level[TID]
        self.__level[TID] += 1
        self.__entries.append((self.clock(), func, level, TID, True))

        try:
            return func(*args, **kwargs)
        except:
            raise
        finally:
            self.__level[TID] -= 1
            self.__entries.append((self.clock(), func, level, TID, False))
    

    def __call__(self, func : Callable[P, R]) -> Callable[P, R]:
        """
        Implements the decorator of a function.
        A function decorated with a chrono will be timed every time it is called.
        """
        from Viper.meta.utils import signature_def, signature_call
        from functools import wraps

        sig = "@wraps(old_target)\n"

        sig_def, env = signature_def(func, init_env = {"old_target" : func, "chrono" : self.call, "wraps" : wraps})
        
        code = sig + sig_def
        
        code += "\n\t"

        code += "return chrono(old_target, "

        sig_call = signature_call(func, decorate = False)

        code += sig_call + ")"
                
        code += "\n"

        exec(code, env)

        return env[func.__name__]
    

    def results(self, extensive : bool = False) -> Dict[Callable, List[ExecutionInfo]]:
        """
        Returns the execution times of all function, in the clock unit.

        Results are in the form:
            {
                func1 : [ExecutionInfo1, ExecutionInfo2, ...],
                func2 : ...,
                ...
            }

        If extensive is True, when a function passes to another timed function, its own chronometer keeps running.
        Otherwise, the second function's time is subtracted from the first one.
        """
        from typing import Dict, List, Callable, Tuple

        if not isinstance(extensive, bool):
            raise TypeError("Expected bool, got " + repr(extensive.__class__.__name__))
        res : Dict[Callable, List[ExecutionInfo]] = {}

        entries = self.__entries.copy()
        TIDs = {TID for time, func, level, TID, entry in entries}
        for TID in TIDs:
            calls : List[Tuple[Callable, int]] = []
            last_durations = [0]
            for time, func, level, TID, entry in filter(lambda x : x[3] == TID, entries):
                if entry:
                    calls.append((func, time))
                    last_durations.append(0)
                else:
                    _, last_time = calls.pop()
                    duration = time - last_time
                    children_duration = last_durations.pop()
                    last_durations[-1] += duration
                    if not extensive:
                        duration -= children_duration
                    if func not in res:
                        res[func] = []
                    result = ExecutionInfo()
                    res[func].append(result)
                    result.function = func
                    result.duration = duration
                    result.level = level
                    result.thread = TID
        
        return res




def __default_conversion(t : int | float) -> float:
    """
    Converts to seconds, assuming a float is in seconds and an integer is in nanoseconds
    """
    if isinstance(t, float):        # Already in seconds
        return t
    elif isinstance(t, int):
        return t / 1000000000       # From nanoseconds to seconds
    else:
        raise TypeError("Unable to automatically convert type '{}' to seconds".format(t.__class__.__name__))


def print_report(c : Chrono, extensive : bool = False, to_seconds : Callable[[Any], float] = __default_conversion):
    """
    Shows a report featuring the average execution time, number of executions and proportions of all functions.
    If you are using a clock with a custom unit, you should give a function to convert your time values to seconds.
    If you are using a second (float) or nanosecond (int) clock the conversion is automatic.
    """
    from typing import Iterable
    from numbers import Complex

    def avg(it : Iterable[Complex]) -> Complex:
        l = list(it)
        if not l:
            raise ValueError("Average of zero values")
        return sum(l) / len(l)

    if not isinstance(c, Chrono):
        raise TypeError("Expected a Chrono object, got " + repr(c.__class__.__name__))
    if not isinstance(extensive, bool):
        raise TypeError("Expected bool, got " + repr(extensive.__class__.__name__))
    from Viper.format import duration

    report = c.results(extensive)
    non_extensive_report = c.results()
    N_func = len(report)
    total_duration = sum(sum(to_seconds(ex_inf.duration) for ex_inf in executions) for executions in non_extensive_report.values())

    if total_duration == 0:
        print("No tests were run (zero total duration)...")
        return

    print("Execution report featuring {} functions or methods, over {}.".format(N_func, duration(total_duration)))
    print("Per function results :")
    
    for func, executions in report.items():
        if hasattr(func, "__module__") and hasattr(func, "__name__"):
            funcname = "'{}.{}'".format(func.__module__, func.__name__)
        elif hasattr(func, "__module__"):
            funcname = "'{}.{}'".format(func.__module__, repr(func))
        else:
            funcname = "'{}'".format(repr(func))
        subtotal_duration = sum(to_seconds(ex_inf.duration) for ex_inf in executions)
        average_duration = avg(to_seconds(ex_inf.duration) for ex_inf in executions)
        proportion = subtotal_duration / total_duration
        n = len(executions)

        print("Function {:<10s}\n\tCalls : {:<5}, Total : {:^10s}, Average : {:^10s}, Proportion : {:^5s}% of the time".format(funcname, str(n), duration(subtotal_duration), duration(average_duration), str(round(proportion * 100, 2))))



del __default_conversion, Any, Callable, Dict, Iterable, List, Optional, ParamSpec, Tuple, TypeVar, Complex, P, R