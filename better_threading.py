"""
This module adds new classes of threads, including one for deamonic threads, but also fallen threads.
"""


import atexit
from concurrent.futures import ThreadPoolExecutor
from threading import Event, RLock, Thread
from typing import Any, Callable, Iterable, Mapping, Set

__all__ = ["Future", "DaemonThread", "FallenThread", "DeamonPoolExecutor"]





class Future(Event):
    
    """
    A Future represents an eventual value. This value might get defined at some point.
    You can wait for it like an event.
    """

    def set(self, value : Any) -> None:
        """
        Sets the value of the Future.
        """
        self.__value = value
        return super().set()
    
    def result(self) -> Any:
        """
        Waits for the Future to be resolved and returns the associated value.
        """
        self.wait()
        return self.__value



class DaemonThread(Thread):

    """
    Just a separate class for deamonic threads.
    """

    def __init__(self, group: None = None, target: Callable[..., Any] | None = None, name: str | None = None, args: Iterable[Any] = (), kwargs: Mapping[str, Any] | None = None) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=True)

    def start(self) -> None:
        self.daemon = True
        return super().start()
    
    @property
    def daemon(self):
        assert self._initialized, "Thread.__init__() not called"
        return True

    @daemon.setter
    def daemon(self, daemonic):
        if daemonic != True:
            raise ValueError("This is a thread of type DeamonThread. You cannot make it not deamonic.")
        if not self._initialized:
            raise RuntimeError("Thread.__init__() not called")
        if self._started.is_set():
            raise RuntimeError("cannot set daemon status of active thread")
        
        self._daemonic = True





class FallenThread(DaemonThread):

    """
    This subclass of deamonic threads will be alerted upon interpreter shutdown and will be given time to finish their tasks if necessary.
    This is done through the finalization_callback function.
    The FallenThread will be judged disposable when its finalization completes.
    """

    _activation_lock = RLock()
    _new_fallen = Event()

    def __init__(self, finalizing_callback : Callable[[], None], group: None = None, target: Callable[..., Any] | None = None, name: str | None = None, args: Iterable[Any] = (), kwargs: Mapping[str, Any] | None = None) -> None:
        with FallenThread._activation_lock:
            super().__init__(group, target, name, args, kwargs)

            from threading import Event

            if not callable(finalizing_callback):
                raise TypeError("Expected callable for finalizing_callback, got " + repr(finalizing_callback.__class__.__name__))
            
            self._finalizing_callback = finalizing_callback
            self._finalizing_event = Event()        # To tell when finalization has started
            FallenThread._new_fallen.set()          # To tell that a new FallenThread has been created



    


@atexit.register
def save_fallen_threads():
    """
    This function is responsible for calling the finalization process. It will:
        - Start a new DeamonThread for each finalization callback
        - Wait for the completion of all finalizations
        - Wait until both tasks are finished
    """

    from threading import enumerate, RLock, Event

    def _finalize(t : FallenThread):
        """
        Just a little handler for notifying ans starting the finalizer
        """
        t._finalizing_event.set()
        try:
            t._finalizing_callback()
        except:
            print("Exception in FallenThread {}'s finalizer :".format(t.name))
            raise

    alive_finalizers : Set[DaemonThread] = set()    # Running finalizer DeamonThreads
    finalization_lock = RLock()                     # Ensure proper transmission of work between the two tasks
    new_finalizing = Event()                        # A new FallenThread has started finalizing
    finished = [False, False]                       # Indicates if both tasks have finished
    checker_lock = RLock()                          # Ensures the correctness when checking for the completion of tasks
    checker_event = Event()                         # Notifies for a checking round

    def _start_finalizers():
        """
        This function will stay alive until the end and wait start the finalizers of all FallenThreads
        """
        while True:
            if not FallenThread._new_fallen.is_set():   # No new fallen -> no work
                with checker_lock:
                    finished[0] = True
                    checker_event.set()
            FallenThread._new_fallen.wait()     # New fallen!
            with checker_lock:
                finished[0] = False

            with FallenThread._activation_lock:     # Handling them
                FallenThread._new_fallen.clear()
                alive_threads = {t for t in enumerate() if isinstance(t, FallenThread) and t.is_alive()}
                for t in alive_threads:

                    if not t._finalizing_event.is_set():    # I should start its finalizer
                        d = DaemonThread(target = _finalize, args = (t, ))
                        d.start()
                        t._finalizing_event.wait()
                        alive_finalizers.add(d)
                        with checker_lock:
                            finished[1] = False     # The other task has some work to do now
                        with finalization_lock:
                            new_finalizing.set()    # Notifying the other task

    def _await_finalizers():
        """
        This function will wait for the completion of all finalizers.
        """
        while True:
            if not new_finalizing.is_set():     # No new running finalizer -> no work
                with checker_lock:
                    finished[1] = True
                    checker_event.set()
            new_finalizing.wait()       # New finalizer running!
            with finalization_lock:
                new_finalizing.clear()
            with checker_lock:
                finished[1] = False

            dead_finalizers : Set[DaemonThread] = set()
            for d in alive_finalizers.copy():   # Joining all running finalizers
                d.join()
                dead_finalizers.add(d)
            alive_finalizers.difference_update(dead_finalizers)     # Clearing them from the running finalizers

    def _check():
        """
        This function will wait until the two previous tasks complete.
        """
        while True:
            checker_event.wait()    # I received a checking notification!
            with checker_lock:
                if all(finished):   # Both tasks finished -> it is really over now
                    break
                checker_event.clear()

    DaemonThread(target = _start_finalizers).start()
    DaemonThread(target = _await_finalizers).start()
    d = DaemonThread(target = _check)   # Checker thread to join
    d.start()
    d.join()




class DeamonPoolExecutor(ThreadPoolExecutor):

    def _adjust_thread_count(self) -> None:

        from concurrent.futures.thread import _worker, _threads_queues
        import weakref
        # if idle threads are available, don't spin new threads
        if self._idle_semaphore.acquire(timeout=0):
            return

        # When the executor gets lost, the weakref callback will wake up
        # the worker threads.
        def weakref_cb(_, q=self._work_queue):
            q.put(None)

        num_threads = len(self._threads)
        if num_threads < self._max_workers:
            thread_name = '%s_%d' % (self._thread_name_prefix or self,
                                     num_threads)
            t = DaemonThread(name=thread_name, target=_worker,
                                 args=(weakref.ref(self, weakref_cb),
                                       self._work_queue,
                                       self._initializer,
                                       self._initargs))
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self._work_queue


    

del save_fallen_threads, Any, Callable, Iterable, Mapping, Set, Event, RLock, Thread, atexit, ThreadPoolExecutor


