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
import sys


class EventDispatchError(Exception):
    def __init__(self, controller, event):
        self.message = "Controller %s cannot dispatch event %s" % (controller.name, str(event))


class NotDirectlyDispatchable(EventDispatchError):
    def __init__(self, event):
        self.message = "Event %s cannot be dispatched directly" % str(event)


class MissingAction(EventDispatchError):
    def __init__(self, controller, event):
        self.message = "Controller %s does not know how to dispatch event %s" % (controller.name, str(event))


class EventRegistrationError(Exception):
    def __init__(self, caused_by=None):
        self.caused_by = caused_by
        self.message = "Event registration error"


class ActionExists(EventRegistrationError):
    def __init__(self, event_tag, action):
        """

        :param event_tag: event that is already registered
        :param action: action that the event is already registered to
        """
        self.message = "Action for event %s already exists in the controller" % event_tag
        self.caused_by = self
        self.event_tag = event_tag
        self.action = action


class Event(object):
    def __init__(self, event_tag_, argv_=None, kwargv_=None):
        self.event_tag = event_tag_
        self.argv = argv_ if argv_ is not None else []
        self.kwargv = kwargv_ if kwargv_ is not None else {}
        self.response = None
        self.exc_info = None  # sys.exc_info() return value if an exception is thrown on event dispatch
        self.queued = False  # set to True when the event is queued, *not* reset after the dispatch
        self.dispatched = False  # set to True after the event has been dispatched

    def __str__(self):
        if self.event_tag:
            return self.event_tag
        return str(self.__class__)

    def is_directly_dispatchable(self):
        return False

    def is_queued(self):
        return self.queued

    def is_dispatched(self):
        return self.dispatched

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
    def __init__(self, action_map=None):
        self.event_queue = Queue.Queue()
        self.name = "Generic controller"
        self.action_map = action_map if action_map is not None else {}

    def register_event(self, event_tag, action, overwrite=False):
        event_tag = str(event_tag)  # we take no chances
        if overwrite or self.action_map.get(event_tag) is None:
            self.action_map[event_tag] = action
        else:
            raise ActionExists(event_tag, self.action_map[event_tag])

    def register_events(self, actions, overwrite=False):
        try:
            for event_tag, action in actions.items():
                self.register_event(event_tag, action, overwrite)
        except ActionExists as a_e:
            raise a_e
        except Exception as e:
            raise EventRegistrationError(e)

    def enqueue_event(self, event):
        last_try = False
        while True:  # try enqueueing the event until successful or all tries are exhausted
            try:
                self.event_queue.put(event)
                event.queued = True
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

    def enqueue_events(self, events):
        for event in events:
            self.enqueue_event(event)

    def process_events(self):
        while True:
            try:
                event = self.event_queue.get_nowait()
            except Queue.Empty:
                return

            try:
                if event.is_directly_dispatchable():
                    event.dispatch()
                else:
                    self.dispatch(event)
            except Exception as e:
                event.exc_info = sys.exc_info()
            finally:
                event.dispatched = True

    def dispatch(self, event):
        method = self.action_map.get(str(event), None)
        if method is None:
            raise MissingAction(self, event)
        event.response = method(*event.argv, **event.kwargv)
