import time
from urllib.parse import urlencode

from _pytest.monkeypatch import MonkeyPatch
from requests_mock.mocker import Mocker as RequestsMocker

from pypi_client.github_auth import AccessToken, github_device_flow


def test_github_device_flow(requests_mock: RequestsMocker, monkeypatch: MonkeyPatch) -> None:
    device_code = '111'
    user_code = '123-456'
    verification_uri = 'https://github.com'
    expires_in = 900
    interval = 1
    access_token = 'aaa-ccc'

    requests_mock.post('https://github.com/login/device/code', text=urlencode({
        'device_code': device_code,
        'user_code': user_code,
        'verification_uri': verification_uri,
        'expires_in': expires_in,
        'interval': interval
    }))

    requests_mock.post('https://github.com/login/oauth/access_token', text=urlencode({
        'access_token': access_token,
    }))

    def noop(s: float) -> None:
        pass

    monkeypatch.setattr(time, "sleep", noop)

    def write_token(access_token: AccessToken) -> None:
        assert access_token

    with github_device_flow(write_token) as verif_codes:
        assert verif_codes
