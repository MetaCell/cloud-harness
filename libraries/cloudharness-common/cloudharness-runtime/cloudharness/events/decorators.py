from cloudharness import log as logger
from cloudharness.events.client import EventClient
from functools import wraps


def send_event(message_type, operation, uid="id"):
    """
    Decorator to send the result of the function as a CDC message into a topic
    if the result is a tuple then index 0 will be used as the object

    Paramers:
        message_type: the type of the message (relates to the object type) e.g. jobs
        operation: the operation on the object e.g. create / update / delete
        uid: the unique identifier attribute of the object, defaults to "id"
    """
    def real_send_event(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if isinstance(result, tuple):
                obj = result[0]
            else:
                obj = result
            try:
                EventClient.send_event(
                    message_type=message_type,
                    operation=operation,
                    func_name=func,
                    func_args=args,
                    func_kwargs=kwargs,
                    uid=uid,
                    obj=obj)
            except Exception as e:
                logger.error('send_event error.', exc_info=True)

            return result
        return wrapper
    return real_send_event
