import unittest

from django.test import SimpleTestCase
from voluptuous import Invalid

from admission.components.panel.panel import PanelComponent


class PanelTest(SimpleTestCase):
    def test_simple_panel(self):
        # FIXME Use new rendering API after upgrade to django_components >= 0.77
        result = PanelComponent().render(
            context_data={
                'title': 'Title',
            },
            slots_data={
                'body': 'Foobar test body',
            },
        )
        self.assertIn('Foobar test body', result)
        self.assertNotIn('<div class="panel-footer clearfix">', result)

    def test_complexe_panel(self):
        # FIXME Use new rendering API after upgrade to django_components >= 0.77
        result = PanelComponent().render(
            context_data={
                'title': 'Title',
            },
            slots_data={
                'body': 'Body test',
                'footer': 'Footer test',
            },
        )
        self.assertIn('Body test', result)
        self.assertIn('<div class="panel-footer clearfix">', result)
        self.assertIn('Footer test', result)

    @unittest.expectedFailure
    def test_bad_title_type(self):
        # FIXME Use new rendering API after upgrade to django_components >= 0.77
        # Current render method does NOT use get_context_data, and thus does not validate data
        with self.assertRaises(Invalid):
            PanelComponent().render(
                context_data={
                    'title': 42,
                },
                slots_data={
                    'body': 'Foobar test body',
                },
            )
