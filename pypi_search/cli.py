import logging

import click
from tabulate import tabulate

from .repo import cache
from .service import get_sorted_packages


def validate_pkg_name(ctx, param, value: str) -> str:
    MIN_LEN = 4
    if len(value) < MIN_LEN:
        raise click.BadParameter(f'name too short, min length={MIN_LEN}')

    return value   


@click.command()
@click.argument('name-search', callback=validate_pkg_name)
@click.option('--min-stars', type=click.IntRange(min=0), default=500)
@click.option('--no-cache', type=click.BOOL, default=False)
@click.option('--verbose', type=click.BOOL, default=False)
def search(name_search: str, min_stars: int, no_cache: bool, verbose: bool):
    """Search python package by name"""

    if no_cache:
        cache.clear()

    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
        
    sorted_packages = get_sorted_packages(name_search, min_stars)

    if pkg_count := len(sorted_packages):
        print(f'Found {pkg_count} packages:')
    else:
        print('No matching packages found')
        return 

    columns = ['name', 'downloads', 'summary', 'version', 'home_page', 'stars', 'releases', 'last_release_date']
    print(tabulate([
        [getattr(pkg, col) for col in columns]
        for pkg in sorted_packages
    ], headers=columns))


if __name__ == '__main__':
    search()
