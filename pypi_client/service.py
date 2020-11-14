import math
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Iterable, List

from tqdm import tqdm

from .repo import (get_all_pkg_names, get_pkg_downloads_info2,
                   get_pkg_github_info, get_pkg_pypi_info)
from .types import Package


def find_packages(name_search: str, show_progress_indicator) -> List[Package]:
    search_phrases = name_search.lower().split(',')
    def name_matches_phrases(pkg_name: str) -> bool:
        return all(
            search_phrase in pkg_name 
            for search_phrase in search_phrases
        )

    all_pkg_names = [name.lower() for name in get_all_pkg_names()]
    matching_pkg_names = [name for name in all_pkg_names if name_matches_phrases(name)]
    with_progress = progress_indicator(len(matching_pkg_names)) if show_progress_indicator else iter

    THREADS = 10
    with ThreadPoolExecutor(THREADS) as executor:
        futures = [
            executor.submit(get_package_info, pkg_name) 
            for pkg_name in matching_pkg_names
        ]

        return [
            future.result() 
            for future in with_progress(as_completed(futures))
        ]


def progress_indicator(total: int):
    def indicator_fn(iterable: Iterable) -> Iterable:
        return tqdm(iterable=iterable, total=total)
    return indicator_fn


def get_package_info(name: str) -> Package:
    pkg = Package(name=name)

    try:
        pypi_info = get_pkg_pypi_info(name) or {}
    except Exception as e:
        warnings.warn(f'failed to get pypi info for {name}: {e}', RuntimeWarning)
    else:
        info = pypi_info.get('info') or {}
        if summary := info.get('summary'):
            pkg.summary = summary
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
        home_page = vcs_url or info.get('home_page')
        if home_page:
            pkg.home_page = home_page

        releases = pypi_info.get('releases') or {}
        if num_releases := len(releases):
            pkg.releases = num_releases
            if upload_times := [
                upload.get('upload_time') 
                for uploads in releases.values()
                for upload in uploads
            ]:
                pkg.last_release_date = max(upload_times)[:10]

    if pkg.releases:
        try:
            pkg.downloads = get_pkg_downloads_info2(name)
        except Exception as e:
            warnings.warn(f'failed to get downloads info for {name}: {e}', RuntimeWarning)

    if pkg.home_page and ('github.com' in pkg.home_page):
        try:
            github_info = get_pkg_github_info(pkg.home_page) or {}
        except Exception as e:
            warnings.warn(f'failed to get github info for {name}: {e}', RuntimeWarning)
        else:
            pkg.stars = github_info.get('stargazers_count')

    pkg.score = _get_score(pkg)

    return pkg


def _get_score(package: Package) -> int:
    if not package.last_release_date:
        return 0

    score: float = 0

    if package.downloads:
        score += math.log10(package.downloads)

    if package.stars:   
        score +=  math.log2(package.stars)

    days_from_last_release = (date.today() - date.fromisoformat(package.last_release_date)).days
    if days_from_last_release <= 30:
        score += 3
    elif days_from_last_release <= 60:
        score += 2
    elif days_from_last_release <= 120:
        score += 1
    elif days_from_last_release > 180:
        score -= 1    
    elif days_from_last_release > 360:
        score -= 2
    else:
        score -= 3    

    return round(score)
