# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
import uuid

from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from admission.contrib.models import DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixLangueRedactionThese,
)
from admission.ddd.parcours_doctoral.jury.domain.model.enums import FormuleDefense
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from reference.tests.factories.language import FrenchLanguageFactory


class DoctorateAdmissionJuryFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admissions
        cls.admission = DoctorateAdmissionFactory(
            training__academic_year=academic_years[0],
            cotutelle=False,
            supervision_group=promoter.process,
            pre_admission_submission_date=datetime.datetime.now(),
            passed_confirmation=True,
        )

        # User with one cdd
        cls.manager = ProgramManagerFactory(education_group=cls.admission.training.education_group).person.user
        cls.update_path = 'admission:doctorate:update:jury-preparation'
        cls.read_path = 'admission:doctorate:jury-preparation'

    def setUp(self):
        self.client.force_login(user=self.manager)

    def test_get_jury_preparation_detail_cdd_user_with_unknown_doctorate(self):
        url = reverse(self.update_path, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_jury_preparation_detail_cdd_user(self):
        url = reverse(self.update_path, args=[self.admission.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('doctorate').uuid,
            str(self.admission.uuid),
        )
        self.assertEqual(
            response.context['form'].initial,
            {
                'titre_propose': self.admission.thesis_proposed_title,
                'formule_defense': self.admission.defense_method,
                'date_indicative': self.admission.defense_indicative_date.isoformat()
                if self.admission.defense_indicative_date
                else None,
                'langue_redaction': self.admission.thesis_language,
                'langue_soutenance': self.admission.defense_language,
                'commentaire': self.admission.comment_about_jury,
            },
        )

    def test_post_jury_preparation_detail_cdd_user(self):
        url = reverse(self.update_path, args=[self.admission.uuid])
        language = FrenchLanguageFactory()

        response = self.client.post(
            url,
            data={
                'titre_propose': 'Nouveau titre',
                'formule_defense': FormuleDefense.FORMULE_2.name,
                'date_indicative': '01/01/2023',
                'langue_redaction': language.pk,
                'langue_soutenance': ChoixLangueRedactionThese.ENGLISH.name,
                'commentaire': 'Nouveau commentaire',
            },
        )

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.admission.uuid))

        updated_admission = DoctorateAdmission.objects.get(
            uuid=self.admission.uuid,
        )
        self.assertEqual(updated_admission.thesis_proposed_title, 'Nouveau titre')
        self.assertEqual(updated_admission.defense_method, FormuleDefense.FORMULE_2.name)
        self.assertEqual(updated_admission.defense_indicative_date, datetime.date(2023, 1, 1))
        self.assertEqual(updated_admission.thesis_language, language)
        self.assertEqual(updated_admission.defense_language, ChoixLangueRedactionThese.ENGLISH.name)
        self.assertEqual(updated_admission.comment_about_jury, 'Nouveau commentaire')
