from unittest import mock

from base.forms.utils.file_field import PDF_MIME_TYPE


class CheckActionLinksMixin:
    def assertActionLinks(self, links, allowed_actions, forbidden_actions):
        self.assertCountEqual(list(links), allowed_actions + forbidden_actions)

        for action in allowed_actions:
            self.assertTrue('url' in links[action], '{} is not allowed'.format(action))

        for action in forbidden_actions:
            self.assertTrue('error' in links[action], '{} is allowed'.format(action))


class OsisDocumentMockTestMixin:
    def setUp(self):
        super().setUp()
        # Mock osis-document
        patcher = mock.patch('osis_document_components.services.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'osis_document_components.services.get_remote_metadata',
            return_value={
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
                'size': 1,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document_components.services.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document_components.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: ['550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'] if value else []
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document_components.services.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document_components.services.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {
            token: {
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
                'size': 1,
            }
            for token in tokens
        }
        self.addCleanup(patcher.stop)


TESTING_CACHE_SETTING = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
