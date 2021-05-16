# type: ignore

from bs4 import BeautifulSoup

from scrapeacademy import context, run

context.request_delay = 1  # wait 1 second between requests
context.headers["User-Agent"] = "Moziiiila"


async def run_simple():
    page = await context.get("https://www.python.jp")
    soup = BeautifulSoup(page, features="html.parser")
    print(soup.title.text)


run(run_simple())
