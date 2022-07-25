import asyncio
from typing import Any, Awaitable, Optional




class IndependantLoop:


    def __init__(self, loop : Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.loop = loop
        from threading import Thread
        Thread(target=self.loop.run_forever, daemon=True).start()
        while not self.loop.is_running():
            pass

    async def run(self, coro : Awaitable, *, timeout : float = float("inf"), default : Any = None):
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

del asyncio, Any, Awaitable, Optional