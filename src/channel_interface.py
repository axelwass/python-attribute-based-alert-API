class _Channel(object):
    """Base class that each channel must inherit from. within this class
    you must define the methods that all of your plugins must implement
    """

    def __init__(self):
        self.description = 'UNKNOWN'

    def send(self, argument):
        """The method that we expect all channels to implement. This is the
        method that our framework will call
        """
        raise NotImplementedError


