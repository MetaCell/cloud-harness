import abc


class NotificationBaseBackend(metaclass=abc.ABCMeta):
    def __init__(self, *args, **kwargs):
        """
        Init the notification backend

        """
        pass

    @abc.abstractmethod
    def send(self):
        """
        Send the notification
        """
        ...
