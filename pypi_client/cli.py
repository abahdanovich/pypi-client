import json
import logging
from importlib.metadata import version
from operator import attrgetter
from typing import Any, List, Optional, TypeVar, Final

import click
from tabulate import tabulate

from . import cache, user_config
from .github_auth import AccessToken, github_device_flow
from .service import find_packages
from .types import Package


@click.group()
@click.version_option(version('pypi-client'))
def cli() -> None:
    pass


@cli.command()
def auth_github() -> None:
    """Log into GitHub"""

    def write_token(access_token: AccessToken) -> None:
        user_config.write_oauth_token(access_token.access_token)

    with github_device_flow(write_token) as verification_codes:
        print(f'Please open {verification_codes.verification_uri} and enter code: {verification_codes.user_code}')
    print('Success')


def validate_pkg_name(ctx: Any, param: Any, value: str) -> str:
    min_len: Final = 3
    if len(value) < min_len:
        raise click.BadParameter(f'name too short, min length={min_len}')

    return value


@cli.command()
@click.argument('name-search', callback=validate_pkg_name)
@click.option('--limit', type=click.IntRange(min=1), help='Max number of items to return')
@click.option('--no-cache', is_flag=True, type=click.BOOL, default=False, help='Clear cache before run')
@click.option('--log-level', type=click.Choice(['ERROR', 'WARN', 'INFO', 'DEBUG']), default='ERROR',
              help='Logging level')
@click.option('--json', "as_json", is_flag=True, type=click.BOOL, default=False, help='Return in json format')
@click.option('--threads', type=click.INT, default=10, help='Number of threads to use')
def search(name_search: str, limit: int, no_cache: bool, log_level: bool, as_json: bool, threads: int) -> None:
    """Search python package by name"""

    if no_cache:
        cache.clear()

    logging.basicConfig(level=log_level)

    try:
        found_packages = find_packages(name_search, click.progressbar, threads)
    except AssertionError as e:
        print(e)
        return

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

    def _enforce_max_width(val: Val, max_width: Optional[int]) -> Val:
        if max_width and isinstance(val, str) and len(val) > max_width:
            return val[:max_width] + '...'

        return val

    print(tabulate([
        [
            _enforce_max_width(getattr(pkg, col), columns_max_width.get(col))
            for col in columns
        ]
        for pkg in sorted_packages
    ], headers=columns))


if __name__ == '__main__':
    cli()
