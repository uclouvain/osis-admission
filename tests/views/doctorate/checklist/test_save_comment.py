# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_comment.models import CommentEntry

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


class SaveCommentViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.second_sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.second_fac_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group
        ).person.user

        cls.default_headers = {'HTTP_HX-Request': 'true'}

    def setUp(self) -> None:
        super().setUp()
        self.admission = DoctorateAdmissionFactory(
            training=self.training,
            submitted=True,
        )

    @freezegun.freeze_time('2021-12-31T08:15')
    def test_submit_a_new_comment(self):
        self.client.force_login(user=self.sic_manager_user)
        url = resolve_url(
            'admission:doctorate:save-comment',
            uuid=self.admission.uuid,
            tab='donnees_personnelles',
        )

        # Check the response
        response = self.client.post(url, data={'donnees_personnelles-comment': 'Test comment'}, **self.default_headers)

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(
            form.fields['comment'].label,
            f'Commentaire (dernière modification par {self.sic_manager_user.person} ' f'le 31/12/2021 à 08:15) :',
        )

        # Check the added comment
        comment_entry = CommentEntry.objects.filter(
            object_uuid=self.admission.uuid,
            tags=['donnees_personnelles'],
        ).first()

        self.assertIsNotNone(comment_entry)
        self.assertEqual(comment_entry.content, 'Test comment')

    def test_submit_an_updated_comment(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:doctorate:save-comment',
            uuid=self.admission.uuid,
            tab='donnees_personnelles',
        )

        with freezegun.freeze_time('2021-12-31T08:15'):
            response = self.client.post(
                url,
                data={'donnees_personnelles-comment': 'Test comment'},
                **self.default_headers,
            )
            # Check the response
            self.assertEqual(response.status_code, 200)

        with freezegun.freeze_time('2021-12-31T08:20'):
            response = self.client.post(
                url,
                data={'donnees_personnelles-comment': 'Test comment 2'},
                **self.default_headers,
            )
            # Check the response
            self.assertEqual(response.status_code, 200)

            form = response.context['form']
            self.assertEqual(
                form.fields['comment'].label,
                f'Commentaire (dernière modification par {self.sic_manager_user.person} ' f'le 31/12/2021 à 08:20) :',
            )

            # Check the added comment
            comment_entry = CommentEntry.objects.filter(
                object_uuid=self.admission.uuid,
                tags=['donnees_personnelles'],
            ).first()

            self.assertIsNotNone(comment_entry)
            self.assertEqual(comment_entry.content, 'Test comment 2')
