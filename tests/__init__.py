import json
from contextlib import contextmanager

from django.db import connections
from django.test import TestCase as BaseTestCase
from django.test.utils import CaptureQueriesContext


class QueriesAssertionsMixin:
    @contextmanager
    def assertNumQueriesLessThan(self, value, using="default", verbose=False):
        with CaptureQueriesContext(connections[using]) as context:
            yield  # your test will be run here
        if verbose:
            msg = "\r\n%s" % json.dumps(context.captured_queries, indent=4)
        else:
            msg = None
        self.assertLess(len(context.captured_queries), value, msg=msg)

    @contextmanager
    def assertQueriesTimingLessThan(self, value, using="default", verbose=False):
        with CaptureQueriesContext(connections[using]) as context:
            yield  # your test will be run here
        if verbose:
            msg = "\r\n%s" % json.dumps(context.captured_queries, indent=4)
        else:
            msg = None
        self.assertLess(sum(float(q["time"]) for q in context.captured_queries), value, msg=msg)


class CheckActionLinksMixin:
    def assertActionLinks(self, links, allowed_actions, forbidden_actions):
        self.assertCountEqual(list(links), allowed_actions + forbidden_actions)

        for action in allowed_actions:
            self.assertTrue('url' in links[action], '{} is not allowed'.format(action))

        for action in forbidden_actions:
            self.assertTrue('error' in links[action], '{} is allowed'.format(action))


class TestCase(QueriesAssertionsMixin, BaseTestCase):
    pass


TESTING_CACHE_SETTING = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
