import logging
import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import List, Optional, Set

from requests.exceptions import HTTPError

from .repo import (get_all_pkg_names, get_pkg_github_repo, get_pkg_pypi_entry,
                   get_pkg_stats, get_top_pupular_pkg_names)
from .types import Package, ProgressBar
from .types.github_repo import GithubRepo
from .types.pepy_tech import PackageStats
from .types.pypi_entry import PypiEntry


def find_packages(name_search: str, progressbar: ProgressBar, threads: int = 10) -> List[Package]:
    search_phrases = name_search.lower().split(',')
    def name_matches_phrases(pkg_name: str) -> bool:
        return all(
            search_phrase in pkg_name
            for search_phrase in search_phrases
        )

    summary_regexps = {
        re.compile(rf".*\b{phrase}\b.*")
        for phrase in search_phrases
    }
    def summary_matches_phrases(pkg_summary: str) -> bool:
        return all(
            regex.match(pkg_summary)
            for regex in summary_regexps
        )

    all_pkg_names = {name.lower() for name in get_all_pkg_names()}
    all_matching_pkg_names: Set[str] = set(filter(name_matches_phrases, all_pkg_names))

    with ThreadPoolExecutor(threads) as executor:
        futures1 = [
            executor.submit(safe_get_pkg_pypi_entry, pkg_name)
            for pkg_name in get_top_pupular_pkg_names()
        ]

        with progressbar(as_completed(futures1), len(futures1)) as bar:
            pypi_entries: List[PypiEntry] = [
                future.result()
                for future in bar
            ]

    pkg_names_matching_by_description = {
        entry.info.name
        for entry in pypi_entries
        if entry and (summary := entry.info.summary) and summary_matches_phrases(summary.lower())
    }
    all_matching_pkg_names |= pkg_names_matching_by_description

    MAX_MATCHING_NAMES = 1000
    assert len(all_matching_pkg_names) <= MAX_MATCHING_NAMES, f'Too many results to consider (max={MAX_MATCHING_NAMES}), try to use more precise filter'

    with ThreadPoolExecutor(threads) as executor:
        futures2 = [
            executor.submit(get_package_info, pkg_name)
            for pkg_name in all_matching_pkg_names
        ]

        with progressbar(as_completed(futures2), len(futures2)) as bar:
            packages: List[Package] = [
                future.result()
                for future in bar
            ]

    return packages


def safe_get_pkg_pypi_entry(name: str) -> Optional[PypiEntry]:
    try:
        return get_pkg_pypi_entry(name)
    except HTTPError as e:
        logging.warn(f'failed to get pypi info for {name}: {e}')
        return None


def get_package_info(name: str) -> Package:
    pkg = Package(name=name)

    try:
        pypi_info: PypiEntry = get_pkg_pypi_entry(name)
    except HTTPError as e:
        logging.warn(f'failed to get pypi info for {name}: {e}')
    else:
        info = pypi_info.info
        pkg.summary = info.summary
        pkg.version = info.version
        pkg.home_page = info.home_page

        if info.project_urls:
            src_url = info.project_urls.Source
            if src_url and any(
                    vcs_name in src_url
                    for vcs_name in ['github', 'bitbucket', 'gitlab']
                ):
                pkg.home_page = src_url

        releases = pypi_info.releases
        if num_releases := len(releases):
            pkg.releases = num_releases
            if upload_days := {
                upload.upload_time.date()
                for uploads in releases.values()
                for upload in uploads
            }:
                pkg.last_release_date = str(max(upload_days))

    if pkg.releases:
        try:
            stats: PackageStats = get_pkg_stats(name)
        except HTTPError as e:
            logging.warn(f'failed to get downloads info for {name}: {e}')
        else:
            all_downloads = stats.downloads
            day_from = date.today() - timedelta(days=90)
            recent_downloads: int = sum([
                sum(version_downloads.values(), 0)
                for stats_day, version_downloads in all_downloads.items()
                if stats_day > day_from
            ], 0)

            pkg.downloads = recent_downloads


    if pkg.home_page and ('github.com' in pkg.home_page):
        try:
            github_repo: GithubRepo = get_pkg_github_repo(pkg.home_page)
        except HTTPError as e:
            logging.warn(f'failed to get github info for {name}: {e}')
        else:
            pkg.stars = github_repo.stargazers_count

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
    elif days_from_last_release <= 180:
        pass
    elif days_from_last_release <= 270:
        score -= 1
    elif days_from_last_release <= 360:
        score -= 2
    else:
        score -= 3

    return round(score)
