class HelpScoutException(Exception):
    pass


class HelpScoutAuthenticationException(HelpScoutException):
    def __init__(self, *args):
        text = ' '.join(str(arg) for arg in args)
        super(HelpScoutAuthenticationException, self).__init__(
            'HelpScout authentication failed: ' + text)


class HelpScoutRateLimitExceededException(HelpScoutException):
    pass
