# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from django.db.models import JSONField
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.contrib.models.cdd_config import CddConfiguration
from admission.ddd.parcours_doctoral.formation.domain.model.enums import CategorieActivite
from admission.tests.factories.roles import CddConfiguratorFactory
from base.tests.factories.person import SuperUserPersonFactory


class CddConfigTestCase(TestCase):
    data = {}

    @classmethod
    def setUpTestData(cls):
        cls.configurator = CddConfiguratorFactory(entity__version__acronym="FOO")
        for field in CddConfiguration._meta.fields:
            if field.name == 'category_labels':
                values = [str(v) for v in dict(CategorieActivite.choices()).values()]
                cls.data[f'{field.name}_en'] = "\n".join(values)
                cls.data[f'{field.name}_fr-be'] = "\n".join(values)
            elif isinstance(field, JSONField):
                cls.data[f'{field.name}_en'] = "Foo\nBarbaz"
                cls.data[f'{field.name}_fr-be'] = "Bar\nBaz"

    def test_cdd_config_access(self):
        url = resolve_url('admission:config:cdd-config:list')
        self.client.force_login(SuperUserPersonFactory().user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cdd_config_list(self):
        url = resolve_url('admission:config:cdd-config:list')
        self.client.force_login(self.configurator.person.user)
        response = self.client.get(url)
        self.assertContains(response, "FOO")

    def test_cdd_config_edit(self):
        url = resolve_url('admission:config:cdd-config:edit', pk=self.configurator.entity_id)
        self.client.force_login(self.configurator.person.user)

        # No config is created
        self.assertEqual(CddConfiguration.objects.count(), 0)

        # But viewing list creates a config
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CddConfiguration.objects.count(), 1)

        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        expected = {
            'en': ['Foo', 'Barbaz'],
            'fr-be': ['Bar', 'Baz'],
        }
        config = CddConfiguration.objects.first()
        self.assertEqual(config.service_types, expected)

        data = self.data.copy()
        values = [str(v) for v in dict(CategorieActivite.choices()).values()][:-2]
        data['category_labels_en'] = "\n".join(values)
        response = self.client.post(url, data)
        self.assertFormError(response, 'form', 'category_labels', _("Number of values mismatch"))
