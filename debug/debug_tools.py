from typing import Any


class timed_print:

    def __init__(self, delay : float = 5) -> None:
        from time import time_ns
        self._timer = time_ns
        self._t = time_ns()
        self._delay = delay
    
    def __call__(self, *args: Any) -> None:
        if (self._timer() - self._t) / 1000000000 > self._delay:
            print(*args)
            self._t = self._timer()



def time_it(func, *args, **kwargs) -> Any:
    """
    Executes a function with given arguments and keyword arguments and prints the time elapsed for its execution.
    Returns what the function returned.
    """
    from time import time_ns
    from format import duration

    t = time_ns()
    res = func(*args, **kwargs)
    t = time_ns() - t
    print("Function took {} to run.".format(duration(t)))
    return res