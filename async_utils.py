"""
This module add asyncio tools to better avoid problems with some implementations.
For example, an instance of IndependantLoop can be used to await a couroutine that will run in another self-handled loop.
"""


import asyncio
from socket import socket
from typing import Any, Awaitable, Callable, Optional, Tuple, TypeVar

__all__ = ["IndependantLoop", "SelectLoop", "BlockingLoop", "sock_poll_recv", "sock_poll_send", "sock_accept"]
if hasattr(asyncio, "ProactorEventLoop"):
    __all__.append("ProactorLoop")


                


T = TypeVar("T")
class IndependantLoop:

    """
    An event loop that will be run in a separate thread.
    Coroutine can be sent to this loop and yet be awaited in another loop.
    """

    __slots__ = {
        "loop" : "The event loop to run in background"
    }


    def __init__(self, loop : Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.loop = loop
        from Viper.better_threading import FallenThread
        FallenThread(target=self.loop.run_forever, finalizing_callback=loop.stop).start()
        while not self.loop.is_running():
            pass

    async def run(self, coro : Awaitable[T], *, timeout : float = float("inf"), default : Any = None) -> T:
        """
        Runs coroutine coro in the background event loop and awaits it in the current loop.
        If given, waits at most timeout and returns default if timeout runs out before coroutine finishes.
        """
        if not isinstance(timeout, float):
            raise TypeError("Expected float for timeout, got " + repr(timeout.__class__.__name__))
        if timeout < 0:
            raise ValueError("Expected positive value for timeout")
        import asyncio 
        loop = asyncio.get_running_loop()
        fut = asyncio.Future(loop = loop)
        async def _run():
            if timeout == float("inf"):
                res = await coro
            else:
                task = asyncio.wait_for(coro, timeout)
                try:
                    res = await task
                except asyncio.TimeoutError:
                    res = default
            loop.call_soon_threadsafe(fut.set_result, res)
        asyncio.run_coroutine_threadsafe(_run(), self.loop)
        await fut
        return fut.result()
    
    async def run_blocking(self, func : Callable[..., T], *args : Any, **kwargs : Any) -> T:
        """
        Executes the blocking function in a separate (deamon) thread with given arguments and keywork arguments and awaits its result.
        """
        from Viper.better_threading import DeamonPoolExecutor
        def run():
            return func(*args, **kwargs)
        return await SelectLoop.run(SelectLoop.loop.run_in_executor(DeamonPoolExecutor(1, "Async-Thread #"), run))
    
    def close(self):
        self.loop.stop()
    
    def __del__(self):
        self.close()




SelectLoop = IndependantLoop(asyncio.SelectorEventLoop())
if hasattr(asyncio, "ProactorEventLoop"):
    ProactorLoop = IndependantLoop(asyncio.ProactorEventLoop())
BlockingLoop = IndependantLoop(asyncio.SelectorEventLoop())



async def sock_poll_recv(sock : socket, timeout : float = 0.0) -> bool:
    """
    Asynchronously waits at most timeout and returns True when a message has been received on th given socket object. Returns False if the timeout has been reached and no message was received.
    By default, the timeout is 0. You can set an infinite timeout.
    """
    try:
        timeout = float(timeout)
    except:
        pass
    from socket import socket
    if not isinstance(sock, socket):
        raise TypeError("Expected socket object, got " + repr(type(sock).__name__))
    if not isinstance(timeout, float):
        raise TypeError("Expected float, got " + repr(type(timeout).__name__))
    if timeout < 0 or timeout == float("nan"):
        raise ValueError("Expected positive timeout, got " + repr(timeout))
    from asyncio import InvalidStateError, Future
    import logging
    fut = Future(loop = SelectLoop.loop)
    def resolve():
        try:
            fut.set_result(True)
        except InvalidStateError:
            pass
        SelectLoop.loop.remove_reader(sock.fileno())
    SelectLoop.loop.add_reader(sock.fileno(), resolve)
    logging.info("Socket {} waiting for reading availability.".format(repr(sock)))
    res = await SelectLoop.run(fut, timeout = timeout, default = False)
    logging.info("Socket {} is ready to be read from.".format(repr(sock)))
    SelectLoop.loop.remove_reader(sock.fileno())
    return res

async def sock_poll_send(sock : socket, timeout : float = 0.0) -> bool:
    """
    Asynchronously waits at most timeout and returns True when the given socket object is ready to send data. Returns False if the timeout has been reached no data can be sent.
    By default, the timeout is 0. You can set an infinite timeout.
    """
    try:
        timeout = float(timeout)
    except:
        pass
    from socket import socket
    if not isinstance(sock, socket):
        raise TypeError("Expected socket object, got " + repr(type(sock).__name__))
    if not isinstance(timeout, float):
        raise TypeError("Expected float, got " + repr(type(timeout).__name__))
    if timeout < 0 or timeout == float("nan"):
        raise ValueError("Expected positive timeout, got " + repr(timeout))
    from asyncio import InvalidStateError, Future
    import logging
    fut = Future(loop = SelectLoop.loop)
    def resolve():
        try:
            fut.set_result(True)
        except InvalidStateError:
            pass
        SelectLoop.loop.remove_writer(sock.fileno())
    SelectLoop.loop.add_writer(sock.fileno(), resolve)
    logging.info("Socket {} waiting for writing availability.".format(repr(sock)))
    res = await SelectLoop.run(fut, timeout = timeout, default = False)
    logging.info("Socket {} is ready to be written to.".format(repr(sock)))
    SelectLoop.loop.remove_writer(sock.fileno())
    return res

async def sock_accept(sock : socket) -> Tuple[socket, Any]:
    """
    Asynchronous version of socket.accept, ** that actually works without blocking the event loop **.
    """
    import logging
    def accept():
        logging.info("Socket {} entering accepting mode.".format(repr(sock)))
        res = sock.accept()
        logging.info("Socket {} just accepted a connection.".format(repr(sock)))
        return res
    return await BlockingLoop.run_blocking(accept)

async def sock_connect(sock : socket, add : Any) -> None:
    """
    Asynchronous version of socket.connect.
    """
    import logging
    def connect():
        logging.info("Socket {} entering connection mode.".format(repr(sock)))
        res = sock.connect(add)
        logging.info("Socket {} just accepted a connection.".format(repr(sock)))
        return res
    return await BlockingLoop.run_blocking(connect)



del asyncio, Any, Awaitable, Callable, Optional, Tuple, TypeVar, T, socket