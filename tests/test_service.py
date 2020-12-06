import json
from datetime import date, timedelta

import click
from _pytest.monkeypatch import MonkeyPatch
from pypi_client import repo
from pypi_client.repo import cache
from pypi_client.service import _get_score, find_packages, get_package_info
from pypi_client.types import Package
from requests_mock.mocker import Mocker as RequestsMocker


def test_get_score() -> None:
    assert _get_score(Package(name='foo')) == 0
    assert _get_score(Package(name='foo', downloads=1000, stars=1000)) == 0
    assert _get_score(Package(name='foo', last_release_date=days_ago(150))) == 0

    assert _get_score(Package(
        name='foo',
        last_release_date=days_ago(150),
        downloads=1000,
        stars=1000
    )) == 13


def test_get_package_info(requests_mock: RequestsMocker, monkeypatch: MonkeyPatch) -> None:
    pkg_name = 'python-foo'
    author = 'foo-inc'
    summary = "Foo lorem ipsum"
    version = "0.1.0"
    home_page = "http://foo-inc.com"
    github_repo_url = f"https://github.com/{author}/{pkg_name}"
    upload_day = days_ago(150)
    stats_day = days_ago(1)
    downloads = 1000
    stars = 1000

    requests_mock.get(f'https://pypi.org/pypi/{pkg_name}/json', text=json.dumps(
        {
            "info": {
                "name": pkg_name,
                "summary": summary,
                "version": version,
                "project_urls": {
                    "Source": github_repo_url
                },
                "home_page": home_page
            },
            "releases": {
                version: [
                    {"upload_time": f'{upload_day}T00:00'}
                ]
            }
        }
    ))

    requests_mock.get(f'https://api.pepy.tech/api/v2/projects/{pkg_name}', text=json.dumps(
        {
            "downloads": {
                stats_day: {
                    version: downloads
                }
            }
        }
    ))

    monkeypatch.setattr(repo, "read_oauth_token", lambda: 'foo')

    requests_mock.get(f'https://api.github.com/repos/{author}/{pkg_name}', text=json.dumps(
        {
            "stargazers_count": stars
        }
    ))

    cache.clear()
    package = get_package_info(pkg_name)
    assert package == Package(**dict(
        name=pkg_name,
        summary=summary,
        version=version,
        home_page=github_repo_url,
        downloads=downloads,
        stars=stars,
        releases=1,
        last_release_date=upload_day,
        score=13
    ))

    requests_mock.get('https://pypi.org/simple/', text=f'''
        <a>{pkg_name}</a>
        <a>some-other-package</a>
    ''')

    requests_mock.get('https://hugovk.github.io/top-pypi-packages/top-pypi-packages-365-days.min.json', text=json.dumps({
        "rows": []
    }))

    cache.clear()
    found_packages = find_packages(pkg_name, click.progressbar)
    assert len(found_packages) == 1

    cache.clear()


def days_ago(days: int) -> str:
    return str(date.today() - timedelta(days=days))
