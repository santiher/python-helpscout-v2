import logging
import time

from functools import partial
try:  # Python 3
    from urllib.parse import urljoin
except ImportError:  # Python 2
    from urlparse import urljoin

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
        """Returns a request to hit the API in a nicer way. E.g.:
        > client = HelpScout(app_id='asdasd', app_secret='1021')
        > client.conversations.get()
        ...
        > client.conversations.delete('/3')


        Parameters
        ----------
        endpoint: str
            One of the endpoints in the API. E.g.: conversations, mailboxes.

        Returns
        -------
        HelpScoutEndpointRequester
            An object that through the get/post/put/patch/delete callable
            attributes forwards the requests to the appropriate get_objects /
            hit client calls.
        """
        return HelpScoutEndpointRequester(self, endpoint)

    def get_objects(self, endpoint, resource_id=None, params=None):
        """Returns the objects from the endpoint filtering by the parameters.

        Parameters
        ----------
        endpoint: str
            One of the endpoints in the API. E.g.: conversations, mailboxes.
        resource_id: int or str or None
            The id of the resource in the endpoint to query.
            E.g.: in "GET /v2/conversations/123 HTTP/1.1" the id would be 123.
            If None is provided, nothing will be done
        params: dict or str or None
            Dictionary with the parameters to send to the url.
            Or the parameters already un url format.

        Returns
        -------
        [HelpScoutObject]
            A list of objects returned by the api.
        """
        cls = HelpScoutObject.cls(endpoint, endpoint)
        results = cls.from_results(
            self.hit(endpoint, 'get', resource_id, params=params))
        if resource_id is not None:
            return results[0]
        return results

    def hit(self, endpoint, method, resource_id=None, data=None, params=None):
        """Hits the api and yields the data.

        Parameters
        ----------
        endpoint: str
            The API endpoint.
        method: str
            The http method to hit the endpoint with.
            One of {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}
        resource_id: int or str or None
            The id of the resource in the endpoint to query.
            E.g.: in "GET /v2/conversations/123 HTTP/1.1" the id would be 123.
            If None is provided, nothing will be done
        data: dict or None
            A dictionary with the data to send to the API as json.
        params: dict or str or None
            Dictionary with the parameters to send to the url.
            Or the parameters already un url format.

        Yields
        -------
        dict
            Dictionary with HelpScout's _embedded data.
        """
        if self.access_token is None:
            self._authenticate()
        url = urljoin(self.base_url, endpoint)
        if resource_id is not None:
            url = urljoin(url + '/', str(resource_id))
        if params:
            if isinstance(params, dict):
                params = '&'.join('%s=%s' % (k, v) for k, v in params.items())
            url = '%s?%s' % (url, params)
        headers = self._authentication_headers()
        r = getattr(requests, method)(url, headers=headers, json=data)
        logger.debug('%s %s' % (method, url))
        ok, status_code = r.ok, r.status_code
        if status_code in (201, 204):
            yield
        elif ok:
            response = r.json()
            for item in self._results_with_pagination(response, method):
                yield item
        elif status_code == 401:
            self._authenticate()
            for item in self.hit(endpoint, method, resource_id, data):
                yield item
        elif status_code == 429:
            self._handle_rate_limit_exceeded()
            for item in self.hit(endpoint, method, resource_id, data):
                yield item
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
            for item in response[EmbeddedKey]:
                yield item
        else:
            yield response[EmbeddedKey]
        next_obj = response.get('_links', {}).get('next', {})
        next_page = None if next_obj is None else next_obj.get('href')
        while next_page:
            headers = self._authentication_headers()
            logger.debug('%s %s' % (method, next_page))
            r = getattr(requests, method)(next_page, headers=headers)
            if r.ok:
                response = r.json()
                if isinstance(response[EmbeddedKey], list):
                    for item in response[EmbeddedKey]:
                        yield item
                else:
                    yield response[EmbeddedKey]
                next_obj = response.get('_links', {}).get('next', {})
                next_page = None if next_obj is None else next_obj.get('href')
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

    def __eq__(self, other):
        """Equality comparison."""
        return (
            self.__class__ is other.__class__ and
            self.app_id == other.app_id and
            self.app_secret == other.app_secret and
            self.base_url == other.base_url and
            self.rate_limit_sleep == other.rate_limit_sleep and
            self.access_token == other.access_token and
            self.sleep_on_rate_limit_exceeded ==
            other.sleep_on_rate_limit_exceeded)

    def __repr__(self):
        """Returns the object as a string."""
        name = self.__class__.__name__
        attrs = (
            'app_id', 'base_url', 'rate_limit_sleep',
            'sleep_on_rate_limit_exceeded')
        values = [getattr(self, attr) for attr in attrs]
        values = [
            '"%s"' % value if isinstance(value, str) else value
            for value in values]
        kwargs = ', '.join(
            '%s=%s' % (attr, value) for attr, value in zip(attrs, values))
        token = '"xxxxxx"' if self.access_token is not None else None
        return '%s(%s, token=%s)' % (name, kwargs, token)

    __str__ = __repr__


class HelpScoutEndpointRequester:

    def __init__(self, client, endpoint):
        """Client wrapper to perform requester.get/post/put/patch/delete.

        Parameters
        ----------
        client: HelpScoutClient
            A help scout client instance to query the API.
        endpoint: str
            One of the endpoints in the API. E.g.: conversations, mailboxes.
        """
        self.client = client
        self.endpoint = endpoint

    def __getattr__(self, method):
        """Catches http methods like get, post, patch, put and delete.

        Parameters
        ----------
        method: str
            The http method to request to the API.

        Returns
        -------
        client.get_objects return value for the *get* method.
        client.hit return value for other methods.
        """
        if method == 'get':
            return partial(self.client.get_objects, self.endpoint)
        return partial(self._yielded_function, method)

    def _yielded_function(self, method, *args, **kwargs):
        """Calls a generator function and calls next.
        It is intended to be used with post, put, patch and delete which do not
        return objects, but as hit is a generator, still have to be nexted.

        Parameters
        ----------
        *args: positional arguments
            Positional arguments after *method* to forward to client.hit .
        *kwargs: keyword arguments
            Keyword arguments after *method* to forward to client.hit.

        Returns
        -------
        client.hit yielded value.
        """
        return next(self.client.hit(self.endpoint, method, *args, **kwargs))

    def __eq__(self, other):
        """Equality comparison."""
        return (self.__class__ is other.__class__ and
                self.endpoint == other.endpoint and
                self.client == other.client)

    def __repr__(self):
        """Returns the object as a string."""
        name = self.__class__.__name__
        return '%s(app_id="%s", endpoint="%s")' % (
            name, self.client.app_id, self.endpoint)

    __str__ = __repr__
