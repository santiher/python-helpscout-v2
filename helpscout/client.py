import logging
import time

from functools import partial
from urllib.parse import urljoin

import requests

from helpscout.exceptions import (HelpScoutException,
                                  HelpScoutAuthenticationException,
                                  HelpScoutRateLimitExceededException)
from helpscout.model import HelpScoutObject


logger = logging.getLogger('HelpScout')
EmbeddedKey = '_embedded'


class HelpScout:

    def __init__(self, app_id, app_secret,
                 base_url='https://api.helpscout.net/v2/',
                 sleep_on_rate_limit_exceeded=True,
                 rate_limit_sleep=10):
        """Help Scout API v2 client wrapper.

        The app credentials are created on the My App section in your profile.
        More about credentials here:
        https://developer.helpscout.com/mailbox-api/overview/authentication/

        Parameters
        ----------
        app_id: str
            The application id.
        app_secret: str
            The application secret.
        base_url: str
            The API's base url.
        sleep_on_rate_limit_exceeded: Boolean
            True to sleep and retry on rate limits exceeded.
            Otherwise raises an HelpScoutRateLimitExceededException exception.
        rate_limit_sleep: int
            Amount of seconds to sleep when the rate limit is exceeded if
            sleep_on_rate_limit_exceeded is True.
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url
        self.sleep_on_rate_limit_exceeded = sleep_on_rate_limit_exceeded
        self.rate_limit_sleep = rate_limit_sleep
        self.access_token = None

    def __getattr__(self, endpoint):
        """Returns the

        Parameters
        ----------
        endpoint: str
            One of the endpoints in the API. E.g.: conversations, mailboxes.

        Returns
        -------
        callable: params -> [HelpScoutObject]
            A callable that given params, returns the objects of the requested
            endpoint.
        """
        return partial(self.get_objects, endpoint)

    def get_objects(self, endpoint, params=None):
        """Returns the objects from the endpoint filtering by the parameters.

        Parameters
        ----------
        endpoint: str
            One of the endpoints in the API. E.g.: conversations, mailboxes.
        params: dict or str or None
            Dictionary with the parameters to send to the url.
            Or the parameters already un url format.

        Returns
        -------
        [HelpScoutObject]
            A list of objects returned by the api.
        """
        if params:
            if isinstance(params, dict):
                params = '&'.join('%s=%s' % (k, v) for k, v in params.items())
            url = '%s?%s' % (endpoint, params)
        else:
            url = endpoint
        cls = HelpScoutObject.cls(endpoint, endpoint)
        return cls.from_results(self.hit(url, 'get'))

    def hit(self, endpoint, method, data=None):
        """Hits the api and yields the data.

        Parameters
        ----------
        endpoint: str
            The API endpoint.
        method: str
            The http method to hit the endpoint with.
            One of {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}
        data: dict or None
            A dictionary with the data to send to the API.

        Yields
        -------
        dict
            Dictionary with HelpScout's _embedded data.
        """
        if self.access_token is None:
            self._authenticate()
        url = urljoin(self.base_url, endpoint)
        headers = self._authentication_headers()
        r = getattr(requests, method)(url, headers=headers, data=data)
        logger.debug('%s %s' % (method, url))
        ok, status_code = r.ok, r.status_code
        if status_code in (201, 204):
            yield
            return
        elif ok:
            response = r.json()
            yield from self._results_with_pagination(response, method)
        elif status_code == 401:
            self._authenticate()
            yield from self.hit(endpoint, method, data)
        elif status_code == 429:
            self._handle_rate_limit_exceeded()
            yield from self.hit(endpoint, method, data)
        else:
            raise HelpScoutException(r.text)

    def _results_with_pagination(self, response, method):
        """Requests and yields pagination results.

        Parameters
        ----------
        response: dict
            A dictionary with a previous api response return value
        method: str
            The http method to hit the endpoint with.
            One of {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}

        Yields
        dict
            The dictionary response from help scout.
        """
        if EmbeddedKey not in response:
            yield response
            return
        if isinstance(response[EmbeddedKey], list):
            yield from response[EmbeddedKey]
        else:
            yield response[EmbeddedKey]
        next_page = response.get('_links', {}).get('next')
        while next_page:
            headers = self._authentication_headers()
            logger.debug('%s %s' % (method, next_page))
            r = getattr(requests, method)(next_page, headers=headers)
            if r.ok:
                response = r.json()
                if isinstance(response[EmbeddedKey], list):
                    yield from response[EmbeddedKey]
                else:
                    yield response[EmbeddedKey]
                next_page = response.get('_links', {}).get('next')
            elif r.status_code == 401:
                self._authenticate()
            elif r.status_code == 429:
                self._handle_rate_limit_exceeded()
            else:
                raise HelpScoutException(r.text)

    def _authenticate(self):
        """Authenticates with the API and gets a token for subsequent requests.
        """
        url = urljoin(self.base_url, 'oauth2/token')
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            }
        logger.debug('post %s' % url)
        r = requests.post(url, data=data)
        if r.ok:
            response = r.json()
            self.access_token = response['access_token']
        else:
            raise HelpScoutAuthenticationException(r.text)

    def _authentication_headers(self):
        """Returns authentication headers."""
        return {
            'Authorization': 'Bearer ' + self.access_token,
            'content-type': 'application/json',
            'charset': 'UTF-8'
            }

    def _handle_rate_limit_exceeded(self):
        """Handles a rate limit exceeded."""
        logger.warning('Rate limit exceeded.')
        if self.sleep_on_rate_limit_exceeded:
            time.sleep(self.rate_limit_sleep)
        else:
            raise HelpScoutRateLimitExceededException()
