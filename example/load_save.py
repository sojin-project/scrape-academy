# type: ignore
from bs4 import BeautifulSoup

from scrapeacademy import context, run


async def save():
    await context.get("https://www.python.jp", name="index")
    await context.get("https://www.python.jp/pages/about.html", name="about")


run(save())


def to_soup(html) -> None:
    return BeautifulSoup(html, features="html.parser")


soup = to_soup(context.load("index"))
print(soup.title.text)

soup = to_soup(context.load("about"))
print(soup.title.text)
