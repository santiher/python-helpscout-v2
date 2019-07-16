class HelpScoutObject(object):

    key = ''

    def __init__(self, api_object):
        """Object build from an API dictionary.
        Variable assignments to initialized objects is not expected to be done.

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
        self._attrs = tuple(sorted(api_object))
        for key, value in api_object.items():
            setattr(self, key, value)

    @classmethod
    def from_results(cls, api_results):
        """Generates HelpScout objects from API results.

        Parameters
        ----------
        api_results: generator({cls.key: [dict]}) or generator(dict)
            A generator returning API responses that cointain a list of
            objects each under the class key.

        Returns
        -------
        [HelpScoutObject]
        """
        results = []
        for api_result in api_results:
            for object_data in api_result.get(cls.key, [api_result]):
                if len(object_data) > 0:
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
        existing_class = globals().get(class_name)
        if existing_class is not None:
            return existing_class
        globals()[class_name] = cls = type(class_name, (cls,), {'key': key})
        return cls

    def __setattr__(self, attr, value):
        """Sets an attribute to an object and adds it to the attributes list.

        Parameters
        ----------
        attr: str
        value: object
        """
        if attr == '_attrs':
            super(HelpScoutObject, self).__setattr__(attr, value)
        elif attr not in self._attrs:
            self._attrs = tuple(sorted(self._attrs + (attr,)))
            super(HelpScoutObject, self).__setattr__(attr, value)
        else:
            super(HelpScoutObject, self).__setattr__(attr, value)

    def __reduce__(self):
        """For pickling with HelpScoutObject."""
        class_attributes = self.__class__.__name__, self.key
        return get_subclass_instance, class_attributes, self.__getstate__()

    def __getstate__(self):
        """Pickle dump implementation."""
        return self._attrs, tuple(getattr(self, attr) for attr in self._attrs)

    def __setstate__(self, state):
        """Pickle load implementation."""
        self._attrs = state[0]
        for attr, value in zip(self._attrs, state[1]):
            setattr(self, attr, value)

    def __eq__(self, other):
        """Equality comparison."""
        if self.__class__ is not other.__class__:
            return False
        if self._attrs != other._attrs:
            return False
        for attr in self._attrs:
            if getattr(self, attr, None) != getattr(other, attr, None):
                return False
        return True

    def __hash__(self):
        """Hash function."""
        def flatten(obj):
            if isinstance(obj, (list, tuple)):
                return tuple(flatten(item) for item in obj)
            elif isinstance(obj, dict):
                return tuple((k, flatten(obj[k])) for k in sorted(obj))
            return obj
        values = tuple(getattr(self, attr) for attr in self._attrs)
        return hash(self._attrs + flatten(values))

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


def get_subclass_instance(class_name, key):
    """Gets a dynamic class from a class name for unpickling.

    Parameters
    ----------
    name: str
        A class name, expected to start with Upper case.

    Returns
    -------
    A helpscout object subclass.
    """
    cls = globals().get(class_name)
    if cls is None:
        cls = type(class_name, (HelpScoutObject,), {'key': key})
        globals()[class_name] = cls
    return cls.__new__(cls)
