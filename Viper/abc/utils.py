"""
This module defines some useful classes used by ABCs of Viper. Concrete implementations of these ABCs might need to use these objects.
"""

from typing import Callable

__all__ = ["Budget"]





class Budget:

    """
    This class represents a ressource that can be increased or decreased, but that must stay positive.
    To take from the budget, you can acquire it like a lock.
    Closing the Budget will make it impossible to increase again.

    It's actually like an accessorized semaphore?
    """

    def __init__(self, init_value : int = 0) -> None:
        if not isinstance(init_value, int):
            raise TypeError(f"Expected int, got '{type(init_value).__name__}'")
        if init_value < 0:
            raise ValueError("Budget must have a non-negative value")
        from threading import RLock, Event
        from typing import Callable
        self.__closed : bool = False
        self.__lock = RLock()
        self.__op_lock = RLock()
        self.__callbacks : list[Callable[["Budget"], None]] = []
        with self.__lock, self.__op_lock:
            self.__value = init_value
            self.__positive_event = Event()
            if init_value > 0:
                self.__positive_event.set()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__value})"
    
    def __str__(self) -> str:
        return str(self.__value)
    
    def add_callback(self, zero_callback : Callable[["Budget"], None]):
        """
        Adds a function to be called each time the Budget reaches zero.
        """
        if not callable(zero_callback):
            raise TypeError(f"Expected callable for zero_callback, got '{type(zero_callback).__name__}'")
        with self.lock:
            self.__callbacks.append(zero_callback)
            if self.value == 0:
                try:
                    zero_callback(self)
                except:
                    raise RuntimeError("Bugdet's callback got an exception when reaching zero")

    def remove_callback(self, zero_callback : Callable[["Budget"], None]):
        """
        Removes a callback if it was registered.
        Silently does nothing if there was no such callback.
        """
        if not callable(zero_callback):
            raise TypeError(f"Expected callable for zero_callback, got '{type(zero_callback).__name__}'")
        with self.lock:
            if zero_callback in self.__callbacks:
                self.__callbacks.remove(zero_callback)

    @property
    def callbacks(self):
        """
        The list of callback functions that are called each time the Budget reaches zero.
        """
        return self.__callbacks.copy()
    
    @property
    def closed(self):
        """
        Returns True if the budget is closed.
        """
        return self.__closed
    
    def close(self, *, erase : bool = False):
        """
        Closes the budget:
        - Sets its value to zero if erase is True.
        - Sets internal flag to True, so threads waiting to acquire the budget will acquire it even if it is empty.
        """
        if not isinstance(erase, bool):
            raise TypeError(f"Expected bool for erase, got '{type(erase).__name__}'")
        with self.__op_lock:
            self.__closed = True
            self.__positive_event.set()
            if erase:
                self.__value = 0
    
    @property
    def value(self) -> int:
        """
        The current value of the budget.
        """
        return self.__value
    
    # @value.setter
    # def value(self, val : int):
    #     """
    #     Sets the value of the budget. If it is greater than the current value, does not block. Otherwise, acquires the budget first.
    #     """
    #     if not isinstance(val, int):
    #         raise TypeError(f"Expected int, got '{type(val).__name__}'")
    #     if val < 0:
    #         raise ValueError("Budget must have a non-negative value")
    #     with self.__op_lock:
    #         if self.__value > val:
    #             with self:
    #                 self.__value = val
    #                 if self.__value == 0:
    #                     if not self.closed:
    #                         self.__positive_event.clear()
    #                     for cb in self.__callbacks:
    #                         try:
    #                             cb(self)
    #                         except:
    #                             raise RuntimeError("Bugdet's callback got an exception when reaching zero")
    #         elif self.__value < val:
    #             if self.closed:
    #                 raise RuntimeError("Budget is closed")
    #             old_value, self.__value = self.__value, val
    #             if old_value == 0 and not self.closed:
    #                 self.__positive_event.set()
    
    @property
    def lock(self):
        """
        The underlying RLock object.
        """
        return self.__lock
    
    def acquire(self, blocking : bool = True, timeout : float = float("inf")):
        """
        Acquires the budget for reduction. The budget must be positive.
        """
        if timeout == float("inf"):
            timeout = -1
        if blocking:
            from time import time_ns
            t = time_ns()
            if self.__lock.acquire(timeout=timeout):
                if timeout != -1:
                    timeout2 = max(timeout - (time_ns() - t) / 1000000000, 0)
                else:
                    timeout2 = None
                if self.closed or self.__positive_event.wait(timeout2):
                    return True
                else:
                    self.__lock.release()
                    return False
            else:
                return False
        else:
            if self.__lock.acquire(False):
                if self.closed or self.__value > 0:
                    return True
                else:
                    self.__lock.release()
                    return False
            else:
                return False
    
    def release(self):
        """
        Releases the budget.
        """
        self.__lock.release()

    def __enter__(self) -> int:
        """
        Implements with self. Acquires the budget, blocking if necessary, and binds its value on entry.
        """
        if not self.acquire():
            raise RuntimeError("Could not acquire budget")
        return self.value
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Implements with self. Acquires the budget, blocking if necessary, and binds its value on entry.
        """
        self.release()

    def increase(self, value : int = 1):
        """
        Increases the budget by the given amount. Does not require that the budget be possessed by the current thread.
        """
        if not isinstance(value, int):
            raise TypeError(f"Expected int, got '{type(value).__name__}'")
        if value < 0:
            raise ValueError(f"Expected a positive value, got {value}")
        if value == 0:
            return
        with self.__op_lock:
            if self.closed:
                raise RuntimeError("Budget is closed")
            old_value, self.__value = self.__value, self.__value + value
            if old_value == 0:
                self.__positive_event.set()
        
    def decrease(self, value : int = 1):
        """
        Decreases the budget by the given amount. Acquires it to do so, blocking if necessary.
        """
        if not isinstance(value, int):
            raise TypeError(f"Expected int, got '{type(value).__name__}'")
        if value < 0:
            raise ValueError(f"Expected a positive value, got {value}")
        if value == 0:
            return
        with self:
            while value > 0:
                with self.__op_lock:
                    old_value, self.__value = self.__value, max(self.__value - value, 0)
                    value -= old_value - self.__value
                    if self.__value == 0:
                        if not self.closed:
                            self.__positive_event.clear()
                        elif value:
                            raise RuntimeError("Budget is closed")
                        for cb in self.__callbacks:
                            try:
                                cb(self)
                            except:
                                raise RuntimeError("Bugdet's callback got an exception when reaching zero")

    def __add__(self, value : int):
        """
        Implements self + value.
        """
        return self.value + value
    
    def __sub__(self, value : int):
        """
        Implements self - value.
        """
        return self.value - value
    
    def __radd__(self, value : int):
        """
        Implements value + self.
        """
        return value + self.value
    
    def __rsub__(self, value : int):
        """
        Implements value - self.
        """
        return value - self.value

    def __iadd__(self, value : int):
        """
        Implements self += value. Equivalent to self.increase(value).
        """
        self.increase(int(value))
        return self
    
    def __isub__(self, value : int):
        """
        Implements self -= value. Equivelent to self.decrease(value).
        """
        self.decrease(int(value))
        return self
    
    def __pos__(self):
        """
        Implements +self.
        """
        return self.value
    
    def __neg__(self):
        """
        Implements -self.
        """
        return -self.value
    
    def __abs__(self):
        """
        Implements abs(self).
        """
        return self.value
    
    def __int__(self):
        """
        Implements int(self).
        """
        return self.value
    
    def __trunc__(self):
        """
        Implements math.trunc(self).
        """
        return self.value
    
    def __floor__(self):
        """
        Implements math.floor(self).
        """
        return self.value
    
    def __ceil__(self):
        """
        Implements math.ceil(self).
        """
        return self.value
    
    def __round__(self, ndigits : int):
        """
        Implements round(self, ndigits).
        """
        return round(self.value, ndigits)
    
    __match_args__ = ("init_value", )

    def __eq__(self, value: object) -> bool:
        if isinstance(value, int):
            return self.value == value
        elif isinstance(value, Budget):
            return self.value == value.value
        else:
            return False
        
    def __lt__(self, value : int):
        """
        Implements self < value.
        """
        return self.value < value
        
    def __le__(self, value : int):
        """
        Implements self <= value.
        """
        return self.value <= value
    
    def __gt__(self, value : int):
        """
        Implements self > value.
        """
        return self.value > value
    
    def __ge__(self, value : int):
        """
        Implements self >= value.
        """
        return self.value >= value
    
    def __bool__(self):
        """
        Implements bool(self).
        """
        return bool(self.__value)
    




del Callable