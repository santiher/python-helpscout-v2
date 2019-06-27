# Help Scout API client

https://developer.helpscout.com/mailbox-api/endpoints/conversations/list/

This package contains a wrapper to query Help Scout's API.

It has only been used with python 3. Python 2 might or might not work.

Information about the available endpoints, objects and other stuff can be found
on the [API's documentation](https://developer.helpscout.com/mailbox-api/).
The client contains as little internal knowledge of the API as possible, mostly
authentication, pagination and how are objects returned.

## Authentication

In order to use the API you need an app id and app secret.

More about credentials can be found in
[helpscout's documentation](https://developer.helpscout.com/mailbox-api/overview/authentication/).

## Examples

### Listing all users

```python
> from helpscout.client import HelpScout
> hs = HelpScout(app_id='ax0912n', app_secret='axon129')
> users = hs.users()
> users[0]
User(id=12391,
     firstName="John",
     lastName="Doe",
     email="john.doe@gmail.com",
     role="user",
     timezone="America/New_York",
     createdAt="2019-01-03T19:00:00Z",
     updatedAt="2019-05-20T18:00:00Z",
     type="user",
     mention="johnny",
     initials="JD",
     _links={'self': {'href': 'https://api.helpscout.net/v2/users/12391'}})
> users[1].id
9320
```

### Hitting the API directly

```python
> from helpscout.client import HelpScout
> hs = HelpScout(app_id='laknsdo', app_secret='12haosd9')
> for mailbox in hs.hit('mailboxes', 'get'):
>      print(mailbox)
{'mailboxes': [
   {'id': 1930,
    'name': 'Fake Support',
    'slug': '0912301u',
    'email': 'support@fake.com',
    'createdAt': '2018-12-20T20:00:00Z',
    'updatedAt': '2019-05-01T16:00:00Z',
    '_links': {
      'fields': {'href': 'https://api.helpscout.net/v2/mailboxes/1930/fields/'},
      'folders': {'href': 'https://api.helpscout.net/v2/mailboxes/1930/folders/'},
      'self': {'href': 'https://api.helpscout.net/v2/mailboxes/1930'}
    }
   }
 ]
}
```

### Listing conversations using a dictionary parameters

```python
> from helpscout.client import HelpScout
> hs = HelpScout(app_id='asd12', app_secret='onas912')
> params = {'status': 'active'}
> conversations = hs.conversations(params)
```

### Listing conversations using a string with parameters

```python
> from helpscout.client import HelpScout
> hs = HelpScout(app_id='asdon123', app_secret='asdoin1')
> params = 'query=(createdAt:[2019-06-20T00:00:00Z TO 2019-06-22T23:59:59Z])'
> conversations = hs.conversations(params)
```
