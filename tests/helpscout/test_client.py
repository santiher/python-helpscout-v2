from unittest import main, TestCase
from unittest.mock import call, MagicMock, patch, PropertyMock

from helpscout.client import EmbeddedKey, HelpScout
from helpscout.exceptions import (HelpScoutException,
                                  HelpScoutAuthenticationException,
                                  HelpScoutRateLimitExceededException)


class TestClient(TestCase):

    app_id = 'app_id'
    app_secret = 'app_secret'
    url = 'http://helpscout.com/api/'
    sleep = True
    seconds = 3

    def _get_client(
            self, app_id=app_id, app_secret=app_secret, url=url, sleep=sleep,
            seconds=seconds, token=None):
        hs = HelpScout(app_id, app_secret, url, sleep, seconds)
        hs.access_token = token
        return hs

    def test_init(self):
        hs = self._get_client()
        self.assertEqual(hs.app_id, self.app_id)
        self.assertEqual(hs.app_secret, self.app_secret)
        self.assertEqual(hs.base_url, self.url)
        self.assertEqual(hs.sleep_on_rate_limit_exceeded, self.sleep)
        self.assertEqual(hs.rate_limit_sleep, self.seconds)
        self.assertEqual(hs.access_token, None)

    def test_get_objects_dict_params(self):
        endpoint, params = 'users', {'id': '10', 'name': 'Mike'}
        hs = self._get_client()
        with patch('helpscout.client.HelpScoutObject') as HelpScoutObject, \
                patch('helpscout.client.HelpScout.hit') as hit:
            HelpScoutObject.cls.return_value = cls = MagicMock()
            hit.return_value = hit_return = 9
            hs.get_objects(endpoint, params)
            HelpScoutObject.cls.assert_called_with(endpoint, endpoint)
            hit.assert_called_with(endpoint + '?id=10&name=Mike', 'get')
            cls.from_results.assert_called_with(hit_return)

    def test_get_objects_str_params(self):
        endpoint, params = 'users', 'id=10&name=Mike'
        hs = self._get_client()
        with patch('helpscout.client.HelpScoutObject') as HelpScoutObject, \
                patch('helpscout.client.HelpScout.hit') as hit:
            HelpScoutObject.cls.return_value = cls = MagicMock()
            hit.return_value = hit_return = 9
            hs.get_objects(endpoint, params)
            HelpScoutObject.cls.assert_called_with(endpoint, endpoint)
            hit.assert_called_with(endpoint + '?id=10&name=Mike', 'get')
            cls.from_results.assert_called_with(hit_return)

    def test_get_objects_no_params(self):
        endpoint, params = 'users', None
        hs = self._get_client()
        with patch('helpscout.client.HelpScoutObject') as HelpScoutObject, \
                patch('helpscout.client.HelpScout.hit') as hit:
            HelpScoutObject.cls.return_value = cls = MagicMock()
            hit.return_value = hit_return = 9
            hs.get_objects(endpoint, params)
            HelpScoutObject.cls.assert_called_with(endpoint, endpoint)
            hit.assert_called_with(endpoint, 'get')
            cls.from_results.assert_called_with(hit_return)

    def test_hit_no_access_token_ok(self):
        endpoint, method = 'users', 'get'
        full_url = self.url + endpoint
        hs_path = 'helpscout.client.HelpScout.'
        hs = self._get_client()
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_results_with_pagination') as pages:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            response = requests.get.return_value = MagicMock()
            response.ok = True
            response.json.return_value = json_response = {'a': 'b'}
            list(hs.hit(endpoint, method))
            # Asserts
            auth.assert_called_once()
            auth_headers.assert_called_once()
            logger.debug.assert_called_once_with(method + ' ' + full_url)
            requests.get.assert_called_once_with(
                full_url, headers=headers, data=None)
            response.json.assert_called_once()
            pages.assert_called_once_with(json_response, method)

    def test_hit_ok(self):
        endpoint, method = 'users', 'get'
        full_url = self.url + endpoint
        hs_path = 'helpscout.client.HelpScout.'
        hs = self._get_client(token='abc')
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_results_with_pagination') as pages:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            response = requests.get.return_value = MagicMock()
            response.ok = True
            response.json.return_value = json_response = {'a': 'b'}
            list(hs.hit(endpoint, method))
            # Asserts
            auth.assert_not_called()
            auth_headers.assert_called_once()
            logger.debug.assert_called_once_with(method + ' ' + full_url)
            requests.get.assert_called_once_with(
                full_url, headers=headers, data=None)
            response.json.assert_called_once()
            pages.assert_called_once_with(json_response, method)

    def test_hit_post_ok(self):
        endpoint, method = 'users', 'post'
        full_url = self.url + endpoint
        hs_path = 'helpscout.client.HelpScout.'
        hs = self._get_client(token='abc')
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_results_with_pagination') as pages:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            response = requests.post.return_value = MagicMock()
            response.status_code = 201
            response.ok = True
            response.json.return_value = {'a': 'b'}
            ret = list(hs.hit(endpoint, method))
            # Asserts
            auth.assert_not_called()
            auth_headers.assert_called_once()
            logger.debug.assert_called_once_with(method + ' ' + full_url)
            requests.post.assert_called_once_with(
                full_url, headers=headers, data=None)
            response.json.assert_not_called()
            pages.assert_not_called()
            self.assertEqual(ret, [None])

    def test_hit_delete_ok(self):
        endpoint, method = 'users', 'delete'
        full_url = self.url + endpoint
        hs_path = 'helpscout.client.HelpScout.'
        hs = self._get_client(token='abc')
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_results_with_pagination') as pages:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            response = requests.delete.return_value = MagicMock()
            response.status_code = 204
            response.ok = True
            response.json.return_value = {'a': 'b'}
            ret = list(hs.hit(endpoint, method))
            # Asserts
            auth.assert_not_called()
            auth_headers.assert_called_once()
            logger.debug.assert_called_once_with(method + ' ' + full_url)
            requests.delete.assert_called_once_with(
                full_url, headers=headers, data=None)
            response.json.assert_not_called()
            pages.assert_not_called()
            self.assertEqual(ret, [None])

    def test_hit_patch_ok(self):
        endpoint, method = 'users', 'patch'
        full_url = self.url + endpoint
        hs_path = 'helpscout.client.HelpScout.'
        hs = self._get_client(token='abc')
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_results_with_pagination') as pages:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            response = requests.patch.return_value = MagicMock()
            response.status_code = 204
            response.ok = True
            response.json.return_value = {'a': 'b'}
            ret = list(hs.hit(endpoint, method))
            # Asserts
            auth.assert_not_called()
            auth_headers.assert_called_once()
            logger.debug.assert_called_once_with(method + ' ' + full_url)
            requests.patch.assert_called_once_with(
                full_url, headers=headers, data=None)
            response.json.assert_not_called()
            pages.assert_not_called()
            self.assertEqual(ret, [None])

    def test_hit_token_expired(self):
        endpoint, method = 'users', 'get'
        full_url = self.url + endpoint
        hs_path = 'helpscout.client.HelpScout.'
        hs = self._get_client(token='abc')
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_results_with_pagination') as pages:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            response = requests.get.return_value = MagicMock()
            type(response).ok = PropertyMock(side_effect=[False, True])
            type(response).status_code = PropertyMock(side_effect=[401, 200])
            response.json.return_value = json_response = {'a': 'b'}
            list(hs.hit(endpoint, method))
            # Asserts
            self.assertEqual(auth_headers.call_count, 2)
            self.assertEqual(
                logger.debug.call_args_list,
                [call(method + ' ' + full_url) for _ in range(2)])
            self.assertEqual(
                requests.get.call_args_list,
                [call(full_url, headers=headers, data=None) for _ in range(2)])
            response.json.assert_called_once()
            pages.assert_called_once_with(json_response, method)
            auth.assert_called_once()

    def test_hit_rate_limit_exceeded(self):
        endpoint, method = 'users', 'get'
        full_url = self.url + endpoint
        hs_path = 'helpscout.client.HelpScout.'
        hs = self._get_client(token='abc')
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_handle_rate_limit_exceeded') as rate_limit, \
                patch(hs_path + '_results_with_pagination') as pages:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            response = requests.get.return_value = MagicMock()
            type(response).ok = PropertyMock(side_effect=[False, True])
            type(response).status_code = PropertyMock(side_effect=[429, 200])
            response.json.return_value = json_response = {'a': 'b'}
            list(hs.hit(endpoint, method))
            # Asserts
            self.assertEqual(auth_headers.call_count, 2)
            self.assertEqual(
                logger.debug.call_args_list,
                [call(method + ' ' + full_url) for _ in range(2)])
            self.assertEqual(
                requests.get.call_args_list,
                [call(full_url, headers=headers, data=None) for _ in range(2)])
            response.json.assert_called_once()
            pages.assert_called_once_with(json_response, method)
            rate_limit.assert_called_once()
            auth.assert_not_called()

    def test_hit_exception(self):
        endpoint, method = 'users', 'get'
        full_url = self.url + endpoint
        hs_path = 'helpscout.client.HelpScout.'
        hs = self._get_client(token='abc')
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_handle_rate_limit_exceeded') as rate_limit, \
                patch(hs_path + '_results_with_pagination') as pages:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            response = requests.get.return_value = MagicMock()
            response.text = 'Error message from help scout'
            type(response).ok = PropertyMock(side_effect=[False, True])
            type(response).status_code = PropertyMock(side_effect=[500, 200])
            response.json.return_value = {'a': 'b'}
            # Call
            with self.assertRaises(HelpScoutException):
                list(hs.hit(endpoint, method))
            # Asserts
            auth_headers.assert_called_once()
            logger.debug.assert_called_once_with(method + ' ' + full_url)
            requests.get.assert_called_once_with(
                full_url, headers=headers, data=None)
            response.json.assert_not_called()
            pages.assert_not_called()
            rate_limit.assert_not_called()
            auth.assert_not_called()

    def test_pagination_no_embedded(self):
        response = {'msg': 'welcome to help scout'}
        hs = self._get_client(token='abc')
        ret = list(hs._results_with_pagination(response, 'get'))
        self.assertEqual(ret, [response])

    def test_pagination_embedded_single(self):
        response = {EmbeddedKey: {'msg': 'hello', '_links': {'next': None}}}
        hs = self._get_client(token='abc')
        ret = list(hs._results_with_pagination(response, 'get'))
        self.assertEqual(ret, [response[EmbeddedKey]])

    def test_pagination_embedded_list(self):
        response = {
            EmbeddedKey: [
                {'msg': 'hello'},
                {'msg': 'bye'},
            ],
            '_links': {'next': None}
        }
        hs = self._get_client(token='abc')
        ret = list(hs._results_with_pagination(response, 'get'))
        self.assertEqual(ret, response[EmbeddedKey])

    def test_pagination_embedded_next_page_ok(self):
        method = 'get'
        response_value = {
            EmbeddedKey: [
                {'msg': 'hello'},
                {'msg': 'bye'},
            ],
            '_links': {'next': 'http://helpscout.com/next_page/110'}
        }
        responses_values = [
            {EmbeddedKey: [
                {'msg': 'blink 1'},
                {'msg': 'blink 2'},
                ],
             '_links': {'next': 'http://helpscout.com/next_page/111'}},
            {EmbeddedKey: [
                {'msg': 'see ya'},
                ],
             '_links': {'next': None}},
        ]
        expected = (response_value[EmbeddedKey] +
                    responses_values[0][EmbeddedKey] +
                    responses_values[1][EmbeddedKey])
        hs = self._get_client(token='abc')
        hs_path = 'helpscout.client.HelpScout.'
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_handle_rate_limit_exceeded') as rate_limit:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            responses = [
                MagicMock(ok=True, status_code=200,
                          json=MagicMock(return_value=responses_values[0])),
                MagicMock(ok=True, status_code=200,
                          json=MagicMock(return_value=responses_values[1])),
            ]
            requests.get.side_effect = responses
            # Call
            ret = list(hs._results_with_pagination(response_value, method))
            # Asserts
            self.assertEqual(ret, expected)
            self.assertEqual(auth_headers.call_count, 2)
            self.assertEqual(
                logger.debug.call_args_list,
                [call(method + ' ' + response_value['_links']['next']),
                 call(method + ' ' + responses_values[0]['_links']['next'])])
            self.assertEqual(
                requests.get.call_args_list,
                [call(response_value['_links']['next'], headers=headers),
                 call(responses_values[0]['_links']['next'], headers=headers)
                 ])
            responses[0].json.assert_called_once()
            responses[1].json.assert_called_once()
            auth.assert_not_called()
            rate_limit.assert_not_called()

    def test_pagination_embedded_next_page_token_expired(self):
        method = 'get'
        response_value = {
            EmbeddedKey: [
                {'msg': 'hello'},
                {'msg': 'bye'},
            ],
            '_links': {'next': 'http://helpscout.com/next_page/110'}
        }
        responses_values = [
            {EmbeddedKey: [
                {'msg': 'blink 1'},
                {'msg': 'blink 2'},
                ],
             '_links': {'next': 'http://helpscout.com/next_page/111'}},
            {EmbeddedKey: [
                {'msg': 'see ya'},
                ],
             '_links': {'next': None}},
        ]
        expected = (response_value[EmbeddedKey] +
                    responses_values[0][EmbeddedKey] +
                    responses_values[1][EmbeddedKey])
        hs = self._get_client(token='abc')
        hs_path = 'helpscout.client.HelpScout.'
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_handle_rate_limit_exceeded') as rate_limit:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            responses = [
                MagicMock(ok=False, status_code=401,
                          json=MagicMock(return_value=responses_values[0])),
                MagicMock(ok=True, status_code=200,
                          json=MagicMock(return_value=responses_values[0])),
                MagicMock(ok=True, status_code=200,
                          json=MagicMock(return_value=responses_values[1])),
            ]
            requests.get.side_effect = responses
            # Call
            ret = list(hs._results_with_pagination(response_value, method))
            # Asserts
            self.assertEqual(ret, expected)
            self.assertEqual(auth_headers.call_count, 3)
            self.assertEqual(
                logger.debug.call_args_list,
                [call(method + ' ' + response_value['_links']['next']),
                 call(method + ' ' + response_value['_links']['next']),
                 call(method + ' ' + responses_values[0]['_links']['next'])])
            self.assertEqual(
                requests.get.call_args_list,
                [call(response_value['_links']['next'], headers=headers),
                 call(response_value['_links']['next'], headers=headers),
                 call(responses_values[0]['_links']['next'], headers=headers)
                 ])
            responses[1].json.assert_called_once()
            responses[2].json.assert_called_once()
            auth.assert_called_once()
            rate_limit.assert_not_called()

    def test_pagination_embedded_next_page_rate_limit_exceeded(self):
        method = 'get'
        response_value = {
            EmbeddedKey: [
                {'msg': 'hello'},
                {'msg': 'bye'},
            ],
            '_links': {'next': 'http://helpscout.com/next_page/110'}
        }
        responses_values = [
            {EmbeddedKey: [
                {'msg': 'blink 1'},
                {'msg': 'blink 2'},
                ],
             '_links': {'next': 'http://helpscout.com/next_page/111'}},
            {EmbeddedKey: [
                {'msg': 'see ya'},
                ],
             '_links': {'next': None}},
        ]
        expected = (response_value[EmbeddedKey] +
                    responses_values[0][EmbeddedKey] +
                    responses_values[1][EmbeddedKey])
        hs = self._get_client(token='abc')
        hs_path = 'helpscout.client.HelpScout.'
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger, \
                patch(hs_path + '_authenticate') as auth, \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_handle_rate_limit_exceeded') as rate_limit:
            # Setup
            auth_headers.return_value = headers = {'token': 'abc'}
            responses = [
                MagicMock(ok=False, status_code=429,
                          json=MagicMock(return_value=responses_values[0])),
                MagicMock(ok=True, status_code=200,
                          json=MagicMock(return_value=responses_values[0])),
                MagicMock(ok=True, status_code=200,
                          json=MagicMock(return_value=responses_values[1])),
            ]
            requests.get.side_effect = responses
            # Call
            ret = list(hs._results_with_pagination(response_value, method))
            # Asserts
            self.assertEqual(ret, expected)
            self.assertEqual(auth_headers.call_count, 3)
            self.assertEqual(
                logger.debug.call_args_list,
                [call(method + ' ' + response_value['_links']['next']),
                 call(method + ' ' + response_value['_links']['next']),
                 call(method + ' ' + responses_values[0]['_links']['next'])])
            self.assertEqual(
                requests.get.call_args_list,
                [call(response_value['_links']['next'], headers=headers),
                 call(response_value['_links']['next'], headers=headers),
                 call(responses_values[0]['_links']['next'], headers=headers)
                 ])
            responses[0].json.assert_not_called()
            responses[1].json.assert_called_once()
            responses[2].json.assert_called_once()
            auth.assert_not_called()
            rate_limit.assert_called_once()

    def test_pagination_exception(self):
        method = 'get'
        response_value = {
            EmbeddedKey: [
                {'msg': 'hello'},
                {'msg': 'bye'},
            ],
            '_links': {'next': 'http://helpscout.com/next_page/110'}
        }
        responses_values = [
            {EmbeddedKey: [
                {'msg': 'blink 1'},
                {'msg': 'blink 2'},
                ],
             '_links': {'next': 'http://helpscout.com/next_page/111'}},
            {EmbeddedKey: [
                {'msg': 'see ya'},
                ],
             '_links': {'next': None}},
        ]
        hs = self._get_client(token='abc')
        hs_path = 'helpscout.client.HelpScout.'
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger'), \
                patch(hs_path + '_authenticate'), \
                patch(hs_path + '_authentication_headers') as auth_headers, \
                patch(hs_path + '_handle_rate_limit_exceeded'):
            # Setup
            auth_headers.return_value = {'token': 'abc'}
            responses = [
                MagicMock(ok=False, status_code=500,
                          json=MagicMock(return_value=responses_values[0])),
                MagicMock(ok=True, status_code=200,
                          json=MagicMock(return_value=responses_values[0])),
                MagicMock(ok=True, status_code=200,
                          json=MagicMock(return_value=responses_values[1])),
            ]
            requests.get.side_effect = responses
            # Call
            with self.assertRaises(HelpScoutException):
                list(hs._results_with_pagination(response_value, method))

    def test_authenticate_ok(self):
        hs = self._get_client()
        full_url = self.url + 'oauth2/token'
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            }
        response_value = {'access_token': 'kakaroto'}
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger:
            # Setup
            response = MagicMock()
            response.ok, response.json.return_value = True, response_value
            requests.post.return_value = response
            hs._authenticate()
            # Asserts
            logger.debug.assert_called_with('post ' + full_url)
            requests.post.assert_called_with(full_url, data=data)
            response.json.assert_called_once()
            self.assertEqual(hs.access_token, response_value['access_token'])

    def test_authenticate_bad(self):
        hs = self._get_client()
        full_url = self.url + 'oauth2/token'
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            }
        response_value = {'access_token': 'kakaroto'}
        with patch('helpscout.client.requests') as requests, \
                patch('helpscout.client.logger') as logger:
            # Setup
            response = MagicMock()
            response.ok, response.json.return_value = False, response_value
            requests.post.return_value = response
            # Call
            with self.assertRaises(HelpScoutAuthenticationException):
                hs._authenticate()
            # Asserts
            logger.debug.assert_called_with('post ' + full_url)
            requests.post.assert_called_with(full_url, data=data)
            response.json.assert_not_called()
            self.assertEqual(hs.access_token, None)

    def test_authentication_headers(self):
        token = 'kakaroto'
        expected = {
            'Authorization': 'Bearer kakaroto',
            'content-type': 'application/json',
            'charset': 'UTF-8'
        }
        hs = self._get_client(token=token)
        self.assertEqual(hs._authentication_headers(), expected)

    def test_handle_rate_limit_exceeded_sleep(self):
        hs = self._get_client()
        with patch('helpscout.client.time') as time, \
                patch('helpscout.client.logger') as logger:
            hs._handle_rate_limit_exceeded()
            logger.warning.assert_called_with('Rate limit exceeded.')
            time.sleep.assert_called_with(self.seconds)

    def test_handle_rate_limit_exceeded_exception(self):
        hs = self._get_client(sleep=False)
        with patch('helpscout.client.time') as time, \
                patch('helpscout.client.logger') as logger:
            with self.assertRaises(HelpScoutRateLimitExceededException):
                hs._handle_rate_limit_exceeded()
            logger.warning.assert_called_with('Rate limit exceeded.')
            time.sleep.assert_not_called()


if __name__ == '__main__':
    main()
