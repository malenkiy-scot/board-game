"""
Implements generic controller mechanism that queues and dispatches events
"""

import Queue

class Event(object):
    class NotDirectlyDispatchable(Exception):
        def __init__(self, event):
            self.message = "Event %s cannot be dispatched directly" % str(event)

    def __init__(self, event_tag_=None, method_=None, argv_=None, kwargv_=None):
        self.event_tag = event_tag_
        self.method = method_
        self.argv = argv_
        self.kwargv = kwargv_

    def __str__(self):
        return str(self.__class__)

    def is_directly_dispatchable(self):
        return self.method is not None

    def dispatch(self):
        if not self.is_directly_dispatchable():
            raise self.NotDirectlyDispatchable(self)
        return self.method(*self.argv, **self.kwargv)


class Controller(object):
    # TODO: implement
    pass

