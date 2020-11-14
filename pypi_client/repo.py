import functools
import logging
from typing import Iterator, Optional

import requests
from appdirs import user_cache_dir
from diskcache import Cache
from lxml import html

from .types import GithubRepo, PypiEntry
from .user_config import read_oauth_token

cache = Cache(user_cache_dir('pypi-client', 'PyPI'))


def get_all_pkg_names() -> Iterator[str]:   
    tree: html.HtmlElement = html.fromstring(_get_all_pkgs_html())
    return tree.xpath('//a/text()')


@cache.memoize()
def _get_all_pkgs_html() -> bytes:
    logging.debug('get_all_pkgs_html')
    response = requests.get("https://pypi.org/simple/")
    return response.content 


@cache.memoize()
def get_pkg_pypi_info(pkg_name: str) -> Optional[PypiEntry]:
    logging.debug(f'get_pkg_pypi_info for {pkg_name}')
    response = requests.get(f'https://pypi.org/pypi/{pkg_name}/json')
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()    


@cache.memoize()
def get_pkg_downloads_info(pkg_name: str) -> Optional[int]:
    logging.debug(f'get_pkg_downloads_info for {pkg_name}')
    url = 'https://api.pepy.tech/api/v2/projects/' + pkg_name
    response = requests.get(url)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    body = response.json()
    return body.get('total_downloads')


@cache.memoize()
def get_pkg_github_info(pkg_repo: str) -> Optional[GithubRepo]:
    logging.debug(f'get_pkg_github_info for {pkg_repo}')
    repo_name = pkg_repo.strip('/').split('/')[-2:]
    url = 'https://api.github.com/repos/' + '/'.join(repo_name)
    response = requests.get(url, auth=('token', _get_github_oauth_token()))
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


@functools.lru_cache(maxsize=None)
def _get_github_oauth_token() -> str:
    return read_oauth_token()
