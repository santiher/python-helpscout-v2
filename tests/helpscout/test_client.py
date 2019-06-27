from unittest import TestCase, main
from unittest.mock import MagicMock

from helpscout.client import HelpScout


class TestClient(TestCase):

    def test_init(self):
        pass

    def test_get_objects_dict_params(self):
        pass

    def test_get_objects_str_params(self):
        pass

    def test_get_objects_no_params(self):
        pass

    def test_hit_no_access_token(self):
        pass

    def test_hit_ok(self):
        pass

    def test_hit_token_expired(self):
        pass

    def test_hit_exception(self):
        pass

    def test_pagination_no_embedded(self):
        pass

    def test_pagination_embedded(self):
        pass

    def test_pagination_embedded_ok(self):
        pass

    def test_pagination_embedded_token_expired(self):
        pass

    def test_pagination_embedded_rate_limit_exceeded(self):
        pass

    def test_authenticate_ok(self):
        pass

    def test_authenticate_bad(self):
        pass

    def test_authentication_headers(self):
        pass

    def test_handle_rate_limit_exceeded_sleep(self):
        pass

    def test_handle_rate_limit_exceeded_exception(self):
        pass


if __name__ == '__main__':
    main()
