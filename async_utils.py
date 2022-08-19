"""
This module add asyncio tools to better avoid problems with some implementations.
For example, an instance of IndependantLoop can be used to await a couroutine that will run in another self-handled loop.
"""


import asyncio
from typing import Any, Awaitable, Optional

__all__ = ["IndependantLoop", "SelectLoop"]
if hasattr(asyncio, "ProactorEventLoop"):
    __all__.append("ProactorLoop")




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
        from threading import Thread
        Thread(target=self.loop.run_forever, daemon=True).start()
        while not self.loop.is_running():
            pass

    async def run(self, coro : Awaitable, *, timeout : float = float("inf"), default : Any = None):
        """
        Runs coroutine coro in the background event loop and awaits it in the current loop.
        If given, waits at most timeout and returns default if timeout runs out before coroutine finishes.
        """
        if not isinstance(timeout, float):
            raise TypeError("Expected float for timeout, got " + repr(timeout.__class__.__name__))
        if timeout < 0:
            raise ValueError("Expected positive value for timeout")
        import asyncio 
        fut = asyncio.Future()
        loop = asyncio.get_running_loop()
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




SelectLoop = IndependantLoop(asyncio.SelectorEventLoop())
if hasattr(asyncio, "ProactorEventLoop"):
    ProactorLoop = IndependantLoop(asyncio.ProactorEventLoop())

del asyncio, Any, Awaitable, Optional