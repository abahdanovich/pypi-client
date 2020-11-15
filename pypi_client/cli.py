import json
import logging
from importlib.metadata import version
from operator import attrgetter
from typing import Any, List, Optional, TypeVar

import click
from tabulate import tabulate

from .github_auth import github_device_flow
from .repo import cache
from .service import find_packages
from .types import Package


@click.group()
@click.version_option(version('pypi-client'))
def cli() -> None:
    pass


@cli.command()
def auth_github() -> None:
    """Log into GitHub"""
    with github_device_flow() as verif_codes:
        print(f'Please open {verif_codes.verification_uri} and enter code: {verif_codes.user_code}')
    print('Success')


def validate_pkg_name(ctx: Any, param: Any, value: str) -> str:
    MIN_LEN = 4
    if len(value) < MIN_LEN:
        raise click.BadParameter(f'name too short, min length={MIN_LEN}')

    return value   


@cli.command()
@click.argument('name-search', callback=validate_pkg_name)
@click.option('--limit', type=click.IntRange(min=1))
@click.option('--no-cache', is_flag=True, type=click.BOOL, default=False)
@click.option('--verbose', is_flag=True, type=click.BOOL, default=False)
@click.option('--json', "as_json", is_flag=True, type=click.BOOL, default=False)
@click.option('--threads', type=click.INT, default=10)
def search(name_search: str, limit: int, no_cache: bool, verbose: bool, as_json: bool, threads: int) -> None:
    """Search python package by name"""

    if no_cache:
        cache.clear()

    logging.basicConfig(level=logging.DEBUG if verbose else logging.ERROR)
        
    found_packages = find_packages(name_search, click.progressbar, threads)
    sorted_packages = list(reversed(sorted(found_packages, key=attrgetter('score'))))
    if limit:
        sorted_packages = sorted_packages[:limit]

    print_func = _print_as_json if as_json else _print_as_text
    print_func(sorted_packages)


def _print_as_json(sorted_packages: List[Package]) -> None:
    for pkg in sorted_packages:
        print(json.dumps(pkg.__dict__))


def _print_as_text(sorted_packages: List[Package]) -> None:
    if pkg_count := len(sorted_packages):
        print(f'Found {pkg_count} packages:')
    else:
        print('No matching packages found')
        return 

    columns = ['name', 'downloads', 'summary', 'version', 'home_page', 'stars', 'releases', 'last_release_date']
    columns_max_width = {
        'name': 30,
        'summary': 50,
        'home_page': 50
    }

    Val = TypeVar('Val', str, int)
    def _enforse_max_width(val: Val, max_width: Optional[int]) -> Val:
        if max_width and isinstance(val, str) and len(val) > max_width:
            return val[:max_width] + '...'
        
        return val


    print(tabulate([
        [
            _enforse_max_width(getattr(pkg, col), columns_max_width.get(col)) 
            for col in columns
        ]
        for pkg in sorted_packages
    ], headers=columns))


if __name__ == '__main__':
    cli()
