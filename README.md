# Scrape Academy

Scrape Academy provides a framework and a utility that helps you to develop web scraping applications.


## Install

```sh
pip3 install scrape-academy
```

## Simple web page scraping

Scrape Academy helps you to download web pages to scrape.

```python
# Download a page from https://www.python.jp

from bs4 import BeautifulSoup
from scrapeacademy import context, run

async def run_simple():
    page = await context.get("https://www.python.jp")
    soup = BeautifulSoup(page, features="html.parser")
    print(soup.title.text)

run(run_simple())
```

`scrapeacademy.run()` starts [asyncio](https://docs.python.org/3/library/asyncio.html) event loop and run a scraping function.

In the async function, you can use `context.get()` method to download the page. The `context.get()` throttle the requests to the server. By default, `context.get()` waits 0.1 seconds between requests.

## Cache downloaded files

While developing the scraper, you usually need to investigate the HTML over and over. To help investigations, you can save the downloaded files to the cache directory.

The `context.get()` method saves the downloaded file to the cache directory if `name` parameter is supplied.

```python
# Save https://www.python.jp

from scrapeacademy import context, run

async def save_index():
    page = await context.get("https://www.python.jp", name="python_jp_index")

run(run_simple())
```

Later, you can load the saved HTML from the cache to scrape using another script.

```python
# Parse saved HTML file.

from scrapeacademy import context

html = context.load("python_jp_index")
soup = BeautifulSoup(page, features="html.parser")
print(soup.title.text)
```

## Command-line utility

Scrape Academy provides the `scrapeacademy` command to make development easier.

You can inspect the cached files with a web browser.

```sh
$ scrapeacademy open python_jp_index
```

Or, you can view the file with vi editor as follow.

```sh
$ vi `scrapeacademy path python_jp_index`
```
