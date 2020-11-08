import logging
from typing import Iterator, Optional

# import pypistats
import requests
from appdirs import user_cache_dir
from diskcache import Cache
from lxml import html

from .config import GH_OAUTH_TOKEN
from .types import GithubRepo, PypiEntry

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
        return
    response.raise_for_status()
    return response.json()    


# @cache.memoize()
# def get_pkg_downloads_info1(pkg_name: str) -> Optional[dict]:
#     logging.debug(f'get_pkg_downloads_info1 for {pkg_name}')
#     try:
#         body = json.loads(pypistats.recent(pkg_name, format="json"))
#     except requests.exceptions.HTTPError as e:
#         if e.response.status_code == 404:
#             return
#         raise e
#     data = body.get('data') or {}
#     return data.get('last_month')


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
def get_pkg_github_info(pkg_repo: str) -> Optional[GithubRepo]:
    logging.debug(f'get_pkg_github_info for {pkg_repo}')
    repo_name = pkg_repo.strip('/').split('/')[-2:]
    url = 'https://api.github.com/repos/' + '/'.join(repo_name)
    response = requests.get(url, auth=('token', GH_OAUTH_TOKEN))
    if response.status_code == 404:
        return
    response.raise_for_status()
    return response.json()