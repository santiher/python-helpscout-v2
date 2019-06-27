class HelpScoutObject:

    key = ''

    def __init__(self, api_object):
        """Object build from an API dictionary.

        Parameters
        ----------
        api_object: dict
            Dictionary with an object from the API.
            E.g. attributes for a Mailbox:
            - id
            - name
            - slug
            - email
            - createdAt
            - updatedAt
            - _links
        """
        self._attrs = sorted(api_object)
        for key, value in api_object.items():
            setattr(self, key, value)

    @classmethod
    def from_results(cls, api_results):
        """Generates HelpScout objects from API results.

        Parameters
        ----------
        api_results: generator({cls.key: [dict]})
            A generator returning API responses that cointain a list of
            objects each under the class key.

        Returns
        -------
        [HelpScoutObject]
        """
        results = []
        for api_result in api_results:
            for object_data in api_result[cls.key]:
                results.append(cls(object_data))
        return results

    @classmethod
    def cls(cls, entity_name, key):
        """Returns the object class based on the entity_name.

        Parameters
        ----------
        entity_name: str
            The help scout object name. E.g.: conversation, mailbox.
        key: str
            The key under which the object's dictionary is contained in the
            API response.
            E.g.: conversations, mailboxes.

        Returns
        -------
        type: The object's class
        """
        plural_letters = (-2 if entity_name.endswith('es') else
                          -1 if entity_name.endswith('s') else
                          None)
        class_name = entity_name.capitalize()[:plural_letters]
        return type(class_name, (cls,), {'key': key})

    def __repr__(self):
        """Returns the object as a string."""
        name = self.__class__.__name__
        attrs = self._attrs
        values = [getattr(self, attr) for attr in attrs]
        values = [
            '"%s"' % value if isinstance(value, str) else value
            for value in values]
        kwargs = ', '.join(
            '%s=%s' % (attr, value) for attr, value in zip(attrs, values))
        return '%s(%s)' % (name, kwargs)

    __str__ = __repr__


ObjectKeys = {
    'conversation': 'conversations',
    'mailbox': 'mailboxes',
    }
