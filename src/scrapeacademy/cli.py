import sys
import webbrowser
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, cast
from urllib.request import pathname2url

import click

from .cache import Cache

F = TypeVar("F", bound=Callable[..., Any])


def wrap_exc(f: F) -> F:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except Exception as e:
            raise click.ClickException(str(e))

    return cast(F, wrapper)


@click.group()
@click.option("-d", "--dir", default="./.cache", help="Cache directory")
@click.pass_context
@wrap_exc
def cli(ctx: click.Context, dir: str) -> None:
    ctx.obj = Cache(Path(dir))


@click.command()
@click.argument("name")
@click.pass_context
@wrap_exc
def cat(ctx: click.Context, name: str) -> None:
    """print specified file"""

    cache = cast(Cache, ctx.obj)
    ret = cache.get(name)
    if isinstance(ret, bytes):
        sys.stdout.buffer.write(ret)
    else:
        click.echo(ret)


@click.command()
@click.argument("name")
@click.pass_context
@wrap_exc
def path(ctx: click.Context, name: str) -> None:
    """print file name"""
    cache = cast(Cache, ctx.obj)
    _, path = cache.get_path(name)
    click.echo(str(path))


@click.command()
@click.argument("name")
@click.pass_context
@wrap_exc
def open(ctx: click.Context, name: str) -> None:
    """open file with web browser"""
    cache = cast(Cache, ctx.obj)
    _, path = cache.get_path(name)
    webbrowser.open("file://" + pathname2url(str(path)))


@click.command()
@click.pass_context
@wrap_exc
def list(ctx: click.Context) -> None:
    """list cache contents"""

    cache = cast(Cache, ctx.obj)
    names = cache.list()
    click.echo("\n".join(names))


cli.add_command(cat)
cli.add_command(path)
cli.add_command(open)
cli.add_command(list)
