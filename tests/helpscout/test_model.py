from unittest import TestCase, main

from helpscout.model import HelpScoutObject


class TestHelpScoutObject(TestCase):

    def test_init(self):
        cls = HelpScoutObject.cls('users', 'users')
        user = cls({'id': 12, 'name': 'Mike'})
        self.assertTrue(isinstance(user, cls))
        self.assertTrue(isinstance(user, HelpScoutObject))
        self.assertEqual(user.id, 12)
        self.assertEqual(user.name, 'Mike')
        with self.assertRaises(AttributeError):
            user.email

    def test_from_results(self):
        data = {
            'users': [{'id': 3, 'name': 'Kate'}, {'id': 9, 'name': 'Matt'}]}
        data_generator = (data for _ in range(1))
        cls = HelpScoutObject.cls('users', 'users')
        users = cls.from_results(data_generator)
        self.assertTrue(isinstance(users, list))
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].id, 3)
        self.assertEqual(users[0].name, 'Kate')
        self.assertEqual(users[1].id, 9)
        self.assertEqual(users[1].name, 'Matt')

    def test_from_results_empty(self):
        data = {}
        data_generator = (data for _ in range(1))
        cls = HelpScoutObject.cls('users', 'users')
        users = cls.from_results(data_generator)
        self.assertTrue(isinstance(users, list))
        self.assertEqual(len(users), 0)

    def test_from_results_single(self):
        data = {'id': 9}
        data_generator = (data for _ in range(1))
        cls = HelpScoutObject.cls('users', 'users')
        users = cls.from_results(data_generator)
        self.assertTrue(isinstance(users, list))
        self.assertEqual(len(users), 1)

    def test_entity_class_name(self):
        cls = HelpScoutObject.cls('users', 'users')
        self.assertEqual(cls.__name__, 'User')
        cls = HelpScoutObject.cls('mailboxes', 'mailboxes')
        self.assertEqual(cls.__name__, 'Mailbox')
        cls = HelpScoutObject.cls('rain', 'rain')
        self.assertEqual(cls.__name__, 'Rain')

    def test_class_superclass(self):
        cls = HelpScoutObject.cls('users', 'users')
        self.assertTrue(issubclass(cls, HelpScoutObject))

    def test_cls_name_general_endpoint_top_level(self):
        cls = HelpScoutObject.cls('users', 'users')
        self.assertTrue(cls.__name__, 'users')

    def test_cls_name_top_level_resource_id(self):
        cls = HelpScoutObject.cls('users/120', 'users/120')
        self.assertTrue(cls.__name__, 'users')

    def test_cls_name_down_level_general_endpoint(self):
        endpoint = 'conversations/120/threads'
        cls = HelpScoutObject.cls(endpoint, endpoint)
        self.assertTrue(cls.__name__, 'threads')

    def test_cls_name_down_level_resource_id(self):
        endpoint = 'conversations/120/threads/4'
        cls = HelpScoutObject.cls(endpoint, endpoint)
        self.assertTrue(cls.__name__, 'threads')

    def test_str(self):
        cls = HelpScoutObject.cls('users', 'users')
        user = cls({'id': 12, 'name': 'Mike'})
        self.assertEqual(str(user), 'User(id=12, name="Mike")')


if __name__ == '__main__':
    main()
