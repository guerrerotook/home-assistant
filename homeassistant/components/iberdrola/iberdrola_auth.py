"""This class handle the authentication with the Iberdrola API."""
from asyncio import TimeoutError
import http.cookiejar as cookielib
import json
import logging

from aiohttp import ClientResponseError
from aiohttp.hdrs import METH_POST
import async_timeout

TIMEOUT = 100
_LOGGER = logging.getLogger(__name__)


class IberdrolaAuthentication:
    """Class to perform the Iberdrola Authentication."""

    def __init__(self, session, username: str, password: str) -> None:
        """Init the class."""
        self._username = username
        self._password = password
        self._cookieContainer = cookielib.CookieJar()

    async def login(self):
        """Login in Iberdrola service by simlating a Windows 10 Web App."""
        data = [
            self._username,
            self._password,
            "",
            "Windows 10",
            "PC",
            "Chrome 79.0.3945.130",
            "0",
            "",
            "n",
        ]
        result = await self.post(
            "https://www.i-de.es/consumidores/rest/loginNew/login", data, use_json=False
        )
        self._cookieContainer = result.cookies
        return result

    async def post(self, url, data=None, use_json: bool = True):
        """Execute the POST Request."""

        if use_json and data is not None:
            data = json.dumps(data)
        r = await self.request(METH_POST, url, headers=None, data=data)
        return r

    async def request(self, method, url, data, headers, **kwargs):
        """Execute the request by method and url."""
        try:
            with async_timeout.timeout(TIMEOUT):
                async with self._session.request(
                    method,
                    url,
                    headers=headers,
                    data=data,
                    cookies=self._cookieContainer,
                ) as response:
                    if response.status == 200 or response.status == 202:
                        _LOGGER.info("OK='%s'", response.status)
                        return await response.json()
                    else:
                        _LOGGER.error(
                            "request_info=%s, response.history='%s',  response.status='%s', response.resason='%s'",
                            response.request_info,
                            response.history,
                            response.status,
                            response.reason,
                        )
                        raise ClientResponseError(
                            response.request_info,
                            response.history,
                            status=response.status,
                            message=response.reason,
                        )
        except TimeoutError:
            _LOGGER.error("Timeout")
            raise TimeoutError("Timeout error")
        except Exception as ex:
            _LOGGER.error(ex)
            raise
