class CheckActionLinksMixin:
    def assertActionLinks(self, links, allowed_actions, forbidden_actions):
        self.assertCountEqual(list(links), allowed_actions + forbidden_actions)

        for action in allowed_actions:
            self.assertTrue('url' in links[action], '{} is not allowed'.format(action))

        for action in forbidden_actions:
            self.assertTrue('error' in links[action], '{} is allowed'.format(action))


TESTING_CACHE_SETTING = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
