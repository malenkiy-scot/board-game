import unittest
import event_dispatch


class TestClass(object):
    def __init__(self, result):
        self.result = result

    def doit(self):
        return self.result

    def doit_with_args(self, a, b=1, c=2, d=3):
        return self.result + a + b + c + d

    def throw(self):
        raise UserWarning("blah")


class TestDirectDispatch(unittest.TestCase):
    def setUp(self):
        self.controller = event_dispatch.Controller()
        self.event_doit_1 = event_dispatch.DirectlyDispatchableEvent("mytag1", TestClass(1).doit)
        self.event_doit_with_args = event_dispatch.DirectlyDispatchableEvent("mytag2", TestClass(1).doit_with_args,
                                                                             [10, 20], {'d': 30})
        self.event_throw = event_dispatch.DirectlyDispatchableEvent("mytag3", TestClass(2).throw)

    def test_dispatchable_event(self):
        self.controller.enqueue_event(self.event_doit_1)
        self.assertTrue(self.event_doit_1.is_queued())

        self.controller.process_events()

        self.assertTrue(self.event_doit_1.is_dispatched())
        self.assertEquals(self.event_doit_1.response, 1)

    def test_dispatchable_event_with_args(self):
        self.controller.enqueue_event(self.event_doit_with_args)
        self.assertTrue(self.event_doit_with_args.is_queued())
        self.controller.process_events()

        self.assertTrue(self.event_doit_with_args.is_dispatched())
        self.assertEquals(self.event_doit_with_args.response, 63)

    def test_two_events(self):
        self.controller.enqueue_events((self.event_doit_1, self.event_doit_with_args,))
        self.assertTrue(self.event_doit_1.is_queued())
        self.assertTrue(self.event_doit_with_args.is_queued())
        self.controller.process_events()

        self.assertTrue(self.event_doit_1.is_dispatched())
        self.assertTrue(self.event_doit_with_args.is_dispatched())
        self.assertEquals(self.event_doit_1.response, 1)
        self.assertEquals(self.event_doit_with_args.response, 63)

    def test_dispatch_exception(self):
        self.controller.enqueue_events((self.event_throw, self.event_doit_1,))
        self.assertTrue(self.event_throw.is_queued())
        self.assertTrue(self.event_doit_1.is_queued())
        self.controller.process_events()

        self.assertTrue(self.event_throw.is_dispatched())
        self.assertTrue(self.event_doit_1.is_dispatched())
        self.assertEquals(self.event_doit_1.response, 1)

        self.assertEquals(self.event_throw.exc_info[1].message, 'blah')


class TestControllerDispatch(unittest.TestCase):
    def setUp(self):
        self.controller = event_dispatch.Controller()

        self.method_doit = TestClass(1).doit
        self.method_doit_with_args = TestClass(1).doit_with_args
        self.method_throw = TestClass(2).throw

        self.event_tag1 = event_dispatch.Event('tag1')
        self.event_tag2 = event_dispatch.Event('tag2', [10, 20], {'d': 30})

    def test_no_action(self):
        self.controller.enqueue_event(self.event_tag1)
        self.assertTrue(self.event_tag1.is_queued())

        self.controller.process_events()

        self.assertTrue(self.event_tag1.is_dispatched())
        self.assertEquals(self.event_tag1.exc_info[0], event_dispatch.MissingAction)

    def test_dispatch_ok_by_tag(self):
        self.controller.register_event(self.event_tag1.event_tag, self.method_doit)
        self.controller.enqueue_event(self.event_tag1)
        self.assertTrue(self.event_tag1.is_queued())

        self.controller.process_events()

        self.assertTrue(self.event_tag1.is_dispatched())
        self.assertEquals(self.event_tag1.response, 1)

    def test_dispatch_ok_by_class(self):
        self.event_tag1.event_tag = None
        self.controller.register_event(self.event_tag1.__class__, self.method_doit)
        self.controller.enqueue_event(self.event_tag1)
        self.assertTrue(self.event_tag1.is_queued())

        self.controller.process_events()

        self.assertTrue(self.event_tag1.is_dispatched())
        self.assertEquals(self.event_tag1.response, 1)

    def test_dispatch_ok_with_params(self):
        self.controller.register_event(self.event_tag2.event_tag, self.method_doit_with_args)
        self.controller.enqueue_event(self.event_tag2)
        self.assertTrue(self.event_tag2.is_queued())

        self.controller.process_events()

        self.assertTrue(self.event_tag2.is_dispatched())
        self.assertEquals(self.event_tag2.response, 63)

    def test_dispatch_multiple(self):
        actions = {
            self.event_tag1.event_tag: self.method_throw,
            self.event_tag2.event_tag: self.method_doit_with_args
        }
        self.controller.register_events(actions)

        self.controller.enqueue_event(self.event_tag1)
        self.controller.enqueue_event(self.event_tag2)

        self.assertTrue(self.event_tag1.is_queued())
        self.assertTrue(self.event_tag2.is_queued())

        self.controller.process_events()

        self.assertTrue(self.event_tag1.is_dispatched())
        self.assertTrue(self.event_tag2.is_dispatched())

        self.assertEquals(self.event_tag1.exc_info[1].message, 'blah')
        self.assertEquals(self.event_tag2.response, 63)

    def test_repeated_action(self):
        actions = {
            self.event_tag1.event_tag: self.method_throw,
            self.event_tag2.event_tag: self.method_doit_with_args
        }
        self.controller.register_events(actions)

        with self.assertRaises(event_dispatch.ActionExists):
            self.controller.register_events(actions)
