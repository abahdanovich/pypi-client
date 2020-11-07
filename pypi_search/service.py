import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator, List

from .repo import (get_pkg_downloads_info2, get_pkg_github_info,
                   get_pkg_pypi_info, get_all_pkg_names)
from .types import Package


def get_sorted_packages(name_search: str, min_stars: int) -> List[Package]:
    packages = find_packages(name_search)
    filtered_packages = [
        p for p in packages 
        if (p.stars is None or (p.stars >= min_stars))
            and p.last_release_date
            and (p.downloads or 0) > 0
    ]
    sorted_packages = sorted(filtered_packages, key=lambda p: (p.downloads is not None, p.downloads))
    return list(sorted_packages)


def find_packages(name_search: str) -> Iterator[Package]:
    search_phrases = name_search.lower().split(',')
    def name_matches_phrases(pkg_name: str) -> bool:
        return all(
            search_phrase in pkg_name 
            for search_phrase in search_phrases
        )

    all_pkg_names = [name.lower() for name in get_all_pkg_names()]
    matching_pkg_names = [name for name in all_pkg_names if name_matches_phrases(name)]

    THREADS = 10
    with ThreadPoolExecutor(THREADS) as executor:
        return executor.map(get_package_info, matching_pkg_names)


def get_package_info(name: str) -> Package:
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

    return pkg
