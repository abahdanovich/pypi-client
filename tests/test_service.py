from pypi_client.service import _get_score
from pypi_client.types import Package
from datetime import date, timedelta

def test_get_score() -> None:
    def days_ago(days: int) -> str:
        return str(date.today() - timedelta(days=days))

    assert _get_score(Package(name='foo')) == 0
    assert _get_score(Package(name='foo', downloads=1000, stars=1000)) == 0
    assert _get_score(Package(name='foo', last_release_date=days_ago(150))) == 0
    
    assert _get_score(Package(
        name='foo', 
        last_release_date=days_ago(150),
        downloads=1000
    )) == 3

    assert _get_score(Package(
        name='foo', 
        last_release_date=days_ago(150),
        stars=1000
    )) == 10
