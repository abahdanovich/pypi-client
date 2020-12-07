import functools
import logging
from typing import Iterator, Set

import requests
from lxml import html

from . import cache
from .types.github_repo import GithubRepo
from .types.pepy_tech import PackageStats
from .types.pypi_entry import PypiEntry
from .user_config import read_oauth_token


@cache.memoize()
def get_all_pkg_names() -> Iterator[str]:
    tree: html.HtmlElement = html.fromstring(_get_all_pkgs_html())
    return tree.xpath('//a/text()')


@cache.memoize()
def get_top_popular_pkg_names() -> Set[str]:
    logging.debug('get_top_popular_pkg_names')
    response = requests.get('https://hugovk.github.io/top-pypi-packages/top-pypi-packages-365-days.min.json')
    response.raise_for_status()
    return {r['project'] for r in response.json().get('rows', [])}


@cache.memoize()
def _get_all_pkgs_html() -> str:
    logging.debug('get_all_pkgs_html')
    response = requests.get("https://pypi.org/simple/")
    response.raise_for_status()
    return response.text


@cache.memoize()
def get_pkg_pypi_entry(pkg_name: str) -> PypiEntry:
    logging.debug(f'get_pkg_pypi_entry for {pkg_name}')
    response = requests.get(f'https://pypi.org/pypi/{pkg_name}/json')
    response.raise_for_status()
    return PypiEntry(**response.json())


@cache.memoize()
def get_pkg_stats(pkg_name: str) -> PackageStats:
    logging.debug(f'get_pkg_stats for {pkg_name}')
    url = 'https://api.pepy.tech/api/v2/projects/' + pkg_name
    response = requests.get(url)
    response.raise_for_status()
    return PackageStats(**response.json())


@cache.memoize()
def get_pkg_github_repo(pkg_repo: str) -> GithubRepo:
    logging.debug(f'get_pkg_github_repo for {pkg_repo}')
    repo_name = pkg_repo.strip('/').split('/')[-2:]
    url = 'https://api.github.com/repos/' + '/'.join(repo_name)
    response = requests.get(url, auth=('token', _get_github_oauth_token()))
    response.raise_for_status()
    return GithubRepo(**response.json())


@functools.lru_cache(maxsize=None)
def _get_github_oauth_token() -> str:
    return read_oauth_token()
