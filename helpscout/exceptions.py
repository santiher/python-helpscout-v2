class HelpScoutException(Exception):
    pass


class HelpScoutAuthenticationException(HelpScoutException):
    def __init__(self, *args):
        text = ' '.join(str(arg) for arg in args)
        super().__init__('HelpScout authentication failed: ' + text)


class HelpScoutRateLimitExceededException(HelpScoutException):
    pass
