import json
import logging
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Iterator, List, Optional

import click
import pypistats
import requests
from diskcache import Cache
from lxml import html
from tabulate import tabulate

from .config import GH_OAUTH_TOKEN

cache = Cache('/tmp')
# cache.clear()
logging.basicConfig(level=logging.DEBUG)


@dataclass
class Package:
    name: str
    summary: Optional[str] = None
    version: Optional[str] = None
    home_page: Optional[str] = None
    downloads: Optional[int] = None
    stars: Optional[int] = None
    releases: int = 0
    last_release_date: Optional[str] = None


def find_packages(name_search: str) -> Iterator[Package]:
    pkg_names = search_pkg_names(name_search)
    if not pkg_names:
        return iter([])

    THREADS = 10
    with ThreadPoolExecutor(THREADS) as executor:
        return executor.map(get_package, pkg_names)


def search_pkg_names(substr: str) -> List[str]:   
    tree = html.fromstring(get_all_pkgs_html())
    pkg_names = tree.xpath('//a/text()')
    return filter(lambda pkg_name: substr in pkg_name, pkg_names)


@cache.memoize()
def get_all_pkgs_html():
    logging.debug('get_all_pkgs_html')
    response = requests.get("https://pypi.org/simple/")
    return response.content 


def get_package(name: str) -> Package:
    pkg = Package(name=name)

    try:
        pypi_info = get_pkg_pypi_info(name) or {}
    except Exception as e:
        warnings.warn(f'failed to get pypi info for {name}: {e}', RuntimeWarning)
    else:
        info = pypi_info.get('info') or {}
        if summary := info.get('summary'):
            pkg.summary = summary[:100]
        pkg.version = info.get('version')

        
        vcs_urls = [
            (info.get('project_urls') or {}).get('Source'),
            info.get('home_page')
        ]
        vcs_url = next(iter(
            url
            for url in vcs_urls
            if url and any(
                vcs_name in url 
                for vcs_name in ['github', 'bitbucket', 'gitlab']
            )
        ), None)
        pkg.home_page = vcs_url or info.get('home_page')

        releases = pypi_info.get('releases') or []
        if num_releases := len(releases):
            pkg.releases = num_releases
            if upload_times := [
                upload.get('upload_time') 
                for uploads in releases.values()
                for upload in uploads
            ]:
                pkg.last_release_date = max(upload_times)[:10]

    try:
        if pkg.releases and (downloads := get_pkg_downloads_info2(name)):
            pkg.downloads = downloads
    except Exception as e:
        warnings.warn(f'failed to get downloads info for {name}: {e}', RuntimeWarning)

    if pkg.home_page and ('github.com' in pkg.home_page):
        try:
            github_info = get_pkg_github_info(pkg.home_page) or {}
        except:
            pkg.stars = 0
        else:
            pkg.stars = github_info.get('stargazers_count')

    return pkg


@cache.memoize()
def get_pkg_pypi_info(pkg_name: str) -> Optional[dict]:
    logging.debug(f'get_pkg_pypi_info for {pkg_name}')
    response = requests.get(f'https://pypi.org/pypi/{pkg_name}/json')
    if response.status_code == 404:
        return
    response.raise_for_status()
    return response.json()    


@cache.memoize()
def get_pkg_downloads_info1(pkg_name: str) -> Optional[dict]:
    logging.debug(f'get_pkg_downloads_info1 for {pkg_name}')
    try:
        body = json.loads(pypistats.recent(pkg_name, format="json"))
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return
        raise e
    data = body.get('data') or {}
    return data.get('last_month')


@cache.memoize()
def get_pkg_downloads_info2(pkg_name: str) -> Optional[int]:
    logging.debug(f'get_pkg_downloads_info2 for {pkg_name}')
    url = 'https://api.pepy.tech/api/v2/projects/' + pkg_name
    response = requests.get(url)
    if response.status_code == 404:
        return
    response.raise_for_status()
    body = response.json()
    return body.get('total_downloads')


@cache.memoize()
def get_pkg_github_info(pkg_repo: str) -> Optional[dict]:
    logging.debug(f'get_pkg_github_info for {pkg_repo}')
    repo_name = pkg_repo.strip('/').split('/')[-2:]
    url = 'https://api.github.com/repos/' + '/'.join(repo_name)
    response = requests.get(url, auth=('token', GH_OAUTH_TOKEN))
    if response.status_code == 404:
        return
    response.raise_for_status()
    return response.json()


def validate_pkg_name(ctx, param, value: str) -> str:
    MIN_LEN = 4
    if len(value) < MIN_LEN:
        raise click.BadParameter(f'name too short, min length={MIN_LEN}')

    return value   


@click.command()
@click.argument('name', callback=validate_pkg_name)
@click.option('--min-stars', type=click.IntRange(min=0), default=500)
def search(name, min_stars):
    """Search python package by name"""
    packages = find_packages(name)
    filtered_packages = [
        p for p in packages 
        if (p.stars is None or p.stars >= min_stars)
            and p.last_release_date
            and (p.downloads or 0) > 0
    ]
    if pkg_count := len(filtered_packages):
        print(f'Found {pkg_count} packages:')
    else:
        print('No matching packages found')
        return 
        
    sorted_packages = reversed(sorted(filtered_packages, key=lambda p: (p.downloads is not None, p.downloads)))
    columns = ['name', 'downloads', 'summary', 'version', 'home_page', 'stars', 'releases', 'last_release_date']
    print(tabulate([
        [getattr(pkg, col) for col in columns]
        for pkg in sorted_packages
    ], headers=columns))


if __name__ == '__main__':
    search()


