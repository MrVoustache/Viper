from threading import Event, Thread, get_ident
from typing import Any, Callable, Iterable, Mapping, Optional

SHUTDOWN_TIMEOUT = 1000000000


class DaemonThread(Thread):

    """
    Just a separate class for deamonic threads.
    """

    def __init__(self, group: None = None, target: Optional[Callable[..., Any]] = None, name: Optional[str] = None, args: Iterable[Any] = (), kwargs: Optional[Mapping[str, Any]] = {}) -> None:
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=True)

    def start(self) -> None:
        self.daemon = True
        return super().start()
    
    @property
    def daemon(self):
        assert self._initialized, "Thread.__init__() not called"
        return True

    @daemon.setter
    def daemon(self, daemonic):
        if not self._initialized:
            raise RuntimeError("Thread.__init__() not called")
        if self._started.is_set():
            raise RuntimeError("cannot set daemon status of active thread")
        self._daemonic = True


_alerted = {}

class GuardianThread(Thread):

    """
    Close to deamonic threads, but before when only DeamonThreads and GuardianThreads remain, GuardianThreads will first receive a shutdown signal
    (Through the function better_threading.guardian_exit()) and their callback function will be called.
    After receiving the signal and/or the execution of their callback function, they must exit by themselves.
    Once all GuardianThreads have ended, deamon threads are terminated.
    """

    def __init__(self, group: None = None, target: Optional[Callable[..., Any]] = None, callback : Optional[Callable[[], Any]] = None, name: Optional[str] = None, args: Iterable[Any] = (), kwargs: Optional[Mapping[str, Any]] = {}) -> None:
        if callback != None and not callable(callback):
            raise TypeError("Expected callable for callback, got " + repr(callback.__class__.__name__))
        super().__init__(group = group, target = target, name = name, args = args, kwargs = kwargs, daemon = True)
        self._callback = callback

    
    def start(self) -> None:
        super().start()
        _alerted[self.ident] = [False, self]


_stopping = Event()


def guardian_exit() -> bool:
    from threading import current_thread
    if not isinstance(current_thread(), GuardianThread):
        raise RuntimeError("Non-GuardianThreads cannot know when the Guardians should exit.")
    res = _stopping.is_set()
    if res:
        _alerted[current_thread().ident][0] = True
    return res


def GuardianOfGuardian():
    from time import sleep, time_ns
    from threading import enumerate, current_thread, main_thread
    thread_list = []
    running = True
    main = main_thread()

    while running:
        sleep(0.1)
        new = enumerate()
        if new != thread_list or not main.is_alive():
            thread_list = new
            running = False
            for ti in thread_list:
                if not isinstance(ti, (GuardianThread, DaemonThread)) and not ti.daemon and ti.is_alive() and ti != current_thread():
                    running = True

    _stopping.set()

    def _messenger(target, ident):
        target()
        _alerted[ident][0] = True

    for ti in enumerate():
        if isinstance(ti, GuardianThread) and ti.is_alive() and ti._callback:
            tii = DaemonThread(target = _messenger, args = (ti._callback, ti.ident))
            tii.start()

    while not _alerted:
        sleep(0.0001)
    
    t = time_ns()

    while True:
        elapsed = time_ns() - t

        only_zombies = True
        for status, master in _alerted.values():
            if status and master.is_alive():
                only_zombies = False
        
        if only_zombies and elapsed >= SHUTDOWN_TIMEOUT:
            return

        sleep(0.001)
    
    



GuardianMainThread = Thread(target = GuardianOfGuardian, name = "Guardian of Guardians")
GuardianMainThread.start()

del GuardianMainThread, GuardianOfGuardian, Event, Thread, get_ident, Any, Callable, Iterable, Mapping, Optional

__all__ = ["DaemonThread", "GuardianThread", "guardian_exit"]