# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext

from admission.auth.roles.doctorate_committee_member import DoctorateCommitteeMember
from admission.views.admin.doctorate_committee_members_import import (
    DoctorateCommitteeMembersImportView,
    import_doctorate_committee_members,
    search_education_groups,
    search_persons,
)
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory


class DoctorateCommitteeMembersImportViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_user = UserFactory(is_staff=True)
        cls.other_user = UserFactory()

        cls.person_1 = PersonFactory(first_name='John', last_name='Doe', employee=True)
        cls.person_2 = PersonFactory(first_name='Jane', last_name='Foe', employee=True)
        cls.person_3 = PersonFactory(first_name='Jim', last_name='Poe', employee=True)
        cls.person_4 = PersonFactory(first_name='Jim', last_name='Poe', employee=True)

        cls.entity_version_1 = EntityVersionFactory(acronym='E001')
        cls.entity_version_2a = EntityVersionFactory(acronym='E02A')
        cls.entity_version_2b = EntityVersionFactory(acronym='E02B', entity=cls.entity_version_2a.entity)
        cls.entity_version_3 = EntityVersionFactory(acronym='E003')

        education_group_year_1 = EducationGroupYearFactory(
            management_entity=cls.entity_version_1.entity,
            education_group_type__name=TrainingType.PHD.name,
        )
        education_group_year_2a1 = EducationGroupYearFactory(
            management_entity=cls.entity_version_2a.entity,
            education_group_type__name=TrainingType.PHD.name,
        )
        education_group_year_2a2 = EducationGroupYearFactory(
            management_entity=cls.entity_version_2a.entity,
            education_group=education_group_year_2a1.education_group,
            education_group_type__name=TrainingType.PHD.name,
        )
        education_group_year_2b = EducationGroupYearFactory(
            management_entity=cls.entity_version_2b.entity,
            education_group_type__name=TrainingType.PHD.name,
        )
        education_group_year_3 = EducationGroupYearFactory(
            management_entity=cls.entity_version_3.entity,
            education_group_type__name=TrainingType.PHD.name,
        )

        cls.education_group_1 = education_group_year_1.education_group
        cls.education_group_2 = education_group_year_2a1.education_group
        cls.education_group_3 = education_group_year_3.education_group
        cls.education_group_4 = education_group_year_2b.education_group

        cls.url = resolve_url('admin:admission_doctoratecommitteemember_import')

    def test_search_persons(self):
        persons = search_persons(persons_keys=[])

        self.assertEqual(len(persons), 0)

        persons = search_persons(persons_keys=['John Poe'])

        self.assertEqual(len(persons), 0)

        persons = search_persons(persons_keys=['John Doe', 'Jane Poe', 'Jane Foe', 'Jim Poe'])

        self.assertEqual(len(persons), 7)

        self.assertCountEqual(persons['John Doe'], [self.person_1])
        self.assertCountEqual(persons['Jane Foe'], [self.person_2])
        self.assertCountEqual(persons['Jim Poe'], [self.person_3, self.person_4])
        self.assertCountEqual(persons[self.person_1.global_id], [self.person_1])
        self.assertCountEqual(persons[self.person_2.global_id], [self.person_2])
        self.assertCountEqual(persons[self.person_3.global_id], [self.person_3])
        self.assertCountEqual(persons[self.person_4.global_id], [self.person_4])

    def test_search_education_groups(self):
        education_groups = search_education_groups([])
        self.assertEqual(len(education_groups), 0)

        education_groups = search_education_groups(['E001', 'E02A', 'E02B', 'E003', 'E004'])

        self.assertEqual(len(education_groups), 4)

        self.assertCountEqual(education_groups['E001'], [self.education_group_1])
        self.assertCountEqual(education_groups['E02A'], [self.education_group_2, self.education_group_4])
        self.assertCountEqual(education_groups['E02B'], [self.education_group_2, self.education_group_4])
        self.assertCountEqual(education_groups['E003'], [self.education_group_3])

    def test_import_doctorate_committee_members(self):
        results = import_doctorate_committee_members(
            persons_keys_by_cdd_acronym={
                'E001': ['John Doe', 'Jane Poe', 'Jane Foe', 'Jim Poe', self.person_3.global_id],
                'E02A': ['John Doe'],
                'E02B': ['Jane Foe'],
                'E003': [],
                'E004': ['John Doe'],
            }
        )

        self.assertCountEqual(results['persons_not_found'], ['Jane Poe'])
        self.assertCountEqual(results['persons_with_homonyms'], ['Jim Poe'])
        self.assertCountEqual(results['cdds_with_no_training'], ['E004'])

        roles = DoctorateCommitteeMember.objects.all()

        self.assertEqual(len(roles), 7)

        self.assertTrue(any(r.person == self.person_1 and r.education_group == self.education_group_1 for r in roles))
        self.assertTrue(any(r.person == self.person_2 and r.education_group == self.education_group_1 for r in roles))
        self.assertTrue(any(r.person == self.person_3 and r.education_group == self.education_group_1 for r in roles))
        self.assertTrue(any(r.person == self.person_1 and r.education_group == self.education_group_2 for r in roles))
        self.assertTrue(any(r.person == self.person_2 and r.education_group == self.education_group_2 for r in roles))
        self.assertTrue(any(r.person == self.person_1 and r.education_group == self.education_group_4 for r in roles))
        self.assertTrue(any(r.person == self.person_2 and r.education_group == self.education_group_4 for r in roles))
        self.assertFalse(any(r.education_group == self.education_group_3 for r in roles))

    def test_get_form_with_no_staff_user(self):
        self.client.force_login(user=self.other_user)
        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_form_with_staff_user(self):
        self.client.force_login(user=self.staff_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertTrue(form.fields['file'].required)
        self.assertFalse(form.fields['with_header'].required)

    def test_upload_csv_with_header(self):
        self.client.force_login(user=self.staff_user)

        # Create the CSV file
        rows = [
            'cdd,m1,m2,m3,m4',
            f'E001,John Doe,Jane Poe,Jane Foe,Jim Poe,{self.person_3.global_id}',
            'E02A,John Doe',
            'E02B,Jane Foe',
            'E003,,,,',
            'E004,John Doe',
        ]

        csv_content = '\n'.join(rows)

        csv_file = SimpleUploadedFile('test.csv', csv_content.encode('utf-8'), content_type='text/csv')

        response = self.client.post(self.url, {'file': csv_file, 'with_header': 'on'})

        self.assertEqual(response.status_code, 200)

        # Check that messages are displayed
        messages = [m.message for m in response.context.get('messages', [])]

        self.assertEqual(len(messages), 4)

        self.assertIn(gettext('The data import has been completed.'), messages)
        self.assertIn(gettext('No one has been found for:') + ' Jane Poe.', messages)
        self.assertIn(gettext('Several persons have been found for:') + ' Jim Poe.', messages)
        self.assertIn(gettext('No education group has been found for:') + ' E004.', messages)

        # Check that the roles have been created
        roles = DoctorateCommitteeMember.objects.all()

        self.assertEqual(len(roles), 7)

        self.assertTrue(any(r.person == self.person_1 and r.education_group == self.education_group_1 for r in roles))
        self.assertTrue(any(r.person == self.person_2 and r.education_group == self.education_group_1 for r in roles))
        self.assertTrue(any(r.person == self.person_3 and r.education_group == self.education_group_1 for r in roles))
        self.assertTrue(any(r.person == self.person_1 and r.education_group == self.education_group_2 for r in roles))
        self.assertTrue(any(r.person == self.person_2 and r.education_group == self.education_group_2 for r in roles))
        self.assertTrue(any(r.person == self.person_1 and r.education_group == self.education_group_4 for r in roles))
        self.assertTrue(any(r.person == self.person_2 and r.education_group == self.education_group_4 for r in roles))
        self.assertFalse(any(r.education_group == self.education_group_3 for r in roles))

    def test_upload_csv_without_header(self):
        self.client.force_login(user=self.staff_user)

        # Create the CSV file
        csv_content = f'E001,{self.person_4.global_id}'
        csv_file = SimpleUploadedFile('test.csv', csv_content.encode('utf-8'), content_type='text/csv')

        response = self.client.post(self.url, {'file': csv_file})

        self.assertEqual(response.status_code, 200)

        # Check that a message is displayed
        messages = [m.message for m in response.context.get('messages', [])]

        self.assertEqual(len(messages), 1)

        self.assertIn(gettext('The data import has been completed.'), messages)

        # Check that a role is created
        roles = DoctorateCommitteeMember.objects.all()

        self.assertEqual(len(roles), 1)

        self.assertTrue(any(r.person == self.person_4 and r.education_group == self.education_group_1 for r in roles))
