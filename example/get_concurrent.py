# type: ignore

import asyncio

from scrapeacademy import context, run


async def get_concurrent(url):
    # Get a same page 10 times simultaneously
    tasks = [context.get(url) for _ in range(10)]

    n = 1
    while tasks:
        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for result in done:
            print(f"done #{n}", result.result()[:10])
            n += 1

    print("done")


run(get_concurrent("https://www.python.jp/"))
