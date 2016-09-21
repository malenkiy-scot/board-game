"""
Implements generic controller mechanism that queues and dispatches events

Events are objects placed on a controller queue.  A directly dispatchable event already contains all the information
necessary to dispatch it (this can be used to override the controller default event handling).

For other events the controller contains a dictionary mapping event tags to methods.  The event is dispatched
by calling the method, passing to it the parameters specified in the event.  If the event does not have a tag, it's
mapped by it's class string.

The return value of the dispatched call is put in the event response.

Event dispatch never raises exceptions.  All exceptions are caught and put into the event.
"""

import Queue
import logging


class EventDispatchError(Exception):
    def __init__(self, controller, event):
        self.message = "Controller %s cannot dispatch event %s" % (controller.name, str(event))


class NotDirectlyDispatchable(EventDispatchError):
    def __init__(self, event):
        self.message = "Event %s cannot be dispatched directly" % str(event)


class MissingAction(EventDispatchError):
    def __init__(self, controller, event):
        self.message = "Controller %s does not know how to dispatch event %s" % (controller.name, str(event))


class Event(object):
    def __init__(self, event_tag_, argv_=None, kwargv_=None):
        self.event_tag = event_tag_
        self.argv = argv_
        self.kwargv = kwargv_
        self.response = None

    def __str__(self):
        if self.event_tag:
            return self.event_tag
        return str(self.__class__)

    def is_directly_dispatchable(self):
        return False

    def dispatch(self):
        raise NotDirectlyDispatchable(self)


class DirectlyDispatchableEvent(Event):
    def __init__(self, event_tag_=None, method_=None, argv_=None, kwargv_=None):
        Event.__init__(self, event_tag_, argv_, kwargv_)
        self.method = method_

    def is_directly_dispatchable(self):
        return True

    def dispatch(self):
        self.response = self.method(*self.argv, **self.kwargv)


class Controller(object):
    def __init__(self, action_map = None):
        self.event_queue = Queue.Queue()
        self.name = "Generic controller"
        self.action_map = action_map

    def enqueue_event(self, event):
        last_try = False
        while True:  # try enqueueing the event until successful or all tries are exhausted
            try:
                self.event_queue.put(event)
                break
            except Queue.Full as e:
                if not last_try:
                    # try draining the queue
                    logging.exception("Controller %s queue is full, trying to drain it" % self.name)
                    self.process_events()
                    last_try = True
                else:
                    # nothing we can do
                    logging.error("Controller %s queue is full" % self.name)
                    raise e

    def process_events(self):
        while True:
            try:
                event = self.Queue.get_nowait()
            except Queue.Empty:
                return

            try:
                if event.is_directly_dispatchable():
                    event.dispatch()
                else:
                    self.dispatch(event)
            except Exception as e:
                event.exception = e

    def dispatch(self, event):
        method = self.action_map.get(str(event), None)
        if method is None:
            raise MissingAction(self, event)
        event.response = method(*event.argv, **event.kwargv)