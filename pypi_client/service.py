import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import List

from requests.exceptions import HTTPError

from .repo import (get_all_pkg_names, get_pkg_stats,
                   get_pkg_github_repo, get_pkg_pypi_entry)
from .types import Package, ProgressBar
from .types.pypi_entry import PypiEntry, PypiPackageInfo, PypiProjectUrls


def find_packages(name_search: str, progressbar: ProgressBar, threads: int = 10) -> List[Package]:
    search_phrases = name_search.lower().split(',')
    def name_matches_phrases(pkg_name: str) -> bool:
        return all(
            search_phrase in pkg_name 
            for search_phrase in search_phrases
        )

    all_pkg_names = [name.lower() for name in get_all_pkg_names()]
    matching_pkg_names = [name for name in all_pkg_names if name_matches_phrases(name)]

    with ThreadPoolExecutor(threads) as executor:
        futures = [
            executor.submit(get_package_info, pkg_name) 
            for pkg_name in matching_pkg_names
        ]

        with progressbar(as_completed(futures), len(futures)) as bar:
            return [
                future.result() 
                for future in bar
            ]


def get_package_info(name: str) -> Package:
    pkg = Package(name=name)

    try:
        pypi_info: PypiEntry = get_pkg_pypi_entry(name)
    except HTTPError as e:
        logging.warn(f'failed to get pypi info for {name}: {e}', RuntimeWarning)
    else:
        info = pypi_info.get('info') or PypiPackageInfo(
            summary=None, version=None, project_urls=None, home_page=None
        )
        if summary := info.get('summary'):
            pkg.summary = summary
        pkg.version = info.get('version')

        urls = info.get('project_urls') or PypiProjectUrls(Source=None)
        vcs_urls = [
            urls.get('Source'),
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
            if upload_days := [
                (upload.get('upload_time') or '')[:10] 
                for uploads in releases.values()
                for upload in uploads
            ]:
                pkg.last_release_date = max(upload_days)

    if pkg.releases:
        try:
            stats = get_pkg_stats(name)
            all_downloads = stats['downloads']
            day_from = str(date.today() - timedelta(days=90))
            recent_downloads: int = sum([
                sum((cnt for version, cnt in (version_downloads or {}).items()), 0)
                for day_str, version_downloads in all_downloads.items()
                if day_str > day_from
            ], 0)

            pkg.downloads = recent_downloads
        except HTTPError as e:
            logging.warn(f'failed to get downloads info for {name}: {e}', RuntimeWarning)

    if pkg.home_page and ('github.com' in pkg.home_page):
        try:
            github_repo = get_pkg_github_repo(pkg.home_page)
        except HTTPError as e:
            logging.warn(f'failed to get github info for {name}: {e}', RuntimeWarning)
        else:
            pkg.stars = github_repo['stargazers_count']

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
