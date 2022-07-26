# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.db.models import JSONField
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.contrib.models.cdd_config import CddConfiguration
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import CategorieActivite
from admission.tests.factories.roles import CddManagerFactory
from base.tests.factories.person import SuperUserPersonFactory


class CddConfigTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = CddManagerFactory(entity__version__acronym="FOO")

    def test_cdd_config_access(self):
        url = resolve_url('admission:config:cdd_config:list')
        self.client.force_login(SuperUserPersonFactory().user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cdd_config_list(self):
        url = resolve_url('admission:config:cdd_config:list')
        self.client.force_login(self.manager.person.user)
        response = self.client.get(url)
        self.assertContains(response, "FOO")

    def test_cdd_config_edit(self):
        url = resolve_url('admission:config:cdd_config:edit', pk=self.manager.entity_id)
        self.client.force_login(self.manager.person.user)

        self.assertEqual(CddConfiguration.objects.count(), 0)
        data = {}
        for field in CddConfiguration._meta.fields:
            if field.name == 'category_labels':
                values = [str(v) for v in dict(CategorieActivite.choices()).values()]
                data[f'{field.name}_en'] = "\n".join(values)
                data[f'{field.name}_fr-be'] = "\n".join(values)
            elif isinstance(field, JSONField):
                data[f'{field.name}_en'] = "Foo\nBarbaz"
                data[f'{field.name}_fr-be'] = "Bar\nBaz"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        expected = {
            'en': ['Foo', 'Barbaz'],
            'fr-be': ['Bar', 'Baz'],
        }
        config = CddConfiguration.objects.first()
        self.assertEqual(config.service_types, expected)
