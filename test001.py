import asyncio
from aiohttp import ClientSession
import time


async def fetch(url):
    async with ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()


async def run(loop, r):
    url = "http://127.0.0.1:8888"
    tasks = []
    ts=time.time()
    for i in range(r):
        task = asyncio.ensure_future(fetch(url.format(i)))
        tasks.append(task)
        responses = await asyncio.gather(*tasks)
        # you now have all response bodies in this variable
        print(time.time()-ts)


def print_responses(result):
    print(1)


loop = asyncio.get_event_loop()
future = asyncio.ensure_future(run(loop, 400))
loop.run_until_complete(future)