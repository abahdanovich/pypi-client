import logging
import time
from contextlib import contextmanager
from typing import Callable, Generator
from urllib import parse

import requests

from .types import AccessToken, DeviceFlowVerificationCodes

CLIENT_ID = 'da5e9528b63f1bd10fd8'


@contextmanager
def github_device_flow(write_oauth_token: Callable[[AccessToken], None]) -> Generator[
    DeviceFlowVerificationCodes, None, None
]:
    verification_codes: DeviceFlowVerificationCodes = _get_verification_codes()
    yield verification_codes
    access_token: AccessToken = _wait_for_authorization(verification_codes.device_code, verification_codes.expires_in,
                                                        verification_codes.interval)
    write_oauth_token(access_token)


def _get_verification_codes() -> DeviceFlowVerificationCodes:
    res = requests.post('https://github.com/login/device/code', {'client_id': CLIENT_ID})
    res.raise_for_status()
    r = dict(parse.parse_qsl(res.text))
    return DeviceFlowVerificationCodes(**r)


def _wait_for_authorization(device_code: str, expires_in: int, sleep_interval: int) -> AccessToken:
    time.sleep(sleep_interval)
    expires_in -= sleep_interval

    while expires_in > 0:
        try:
            return _get_access_token(device_code)
        except Exception as e:
            logging.debug(e)
            time.sleep(sleep_interval)
            expires_in -= sleep_interval
    else:
        raise Exception('Verification code expired')


def _get_access_token(device_code: str) -> AccessToken:
    res = requests.post('https://github.com/login/oauth/access_token', {
        'client_id': CLIENT_ID,
        'device_code': device_code,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    })
    res.raise_for_status()
    r = dict(parse.parse_qsl(res.text))

    if 'error' in r:
        raise Exception(r['error_description'], r['error'])

    return AccessToken(**r)
