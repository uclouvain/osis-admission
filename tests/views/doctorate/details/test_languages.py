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
import datetime
import uuid
from typing import List
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.dtos import ConnaissanceLangueDTO
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.language import LanguageKnowledgeFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    CentralManagerRoleFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from osis_profile.models.education import LanguageKnowledge
from osis_profile.models.enums.education import LanguageKnowledgeGrade


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateAdmissionLanguagesDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        # Create admissions
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            submitted_at=datetime.datetime.now(),
        )

        cls.sic_user = CentralManagerRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager = ProgramManagerRoleFactory(
            education_group=cls.admission.training.education_group
        ).person.user

        cls.url = reverse('admission:doctorate:languages', args=[cls.admission.uuid])

    def setUp(self) -> None:
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", "mimetype": "application/pdf", "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_access(self):
        # Anonymous user
        self.client.force_login(user=UserFactory())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

        # SIC
        self.client.force_login(user=self.sic_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Program manager
        self.client.force_login(user=self.program_manager)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_candidate_languages(self):
        self.client.force_login(user=self.sic_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['connaissances_langues'], [])

        # Create some language knowledge
        nl_language: LanguageKnowledge = LanguageKnowledgeFactory(
            language__code='NL',
            person=self.admission.candidate,
            listening_comprehension=LanguageKnowledgeGrade.A1.name,
            speaking_ability=LanguageKnowledgeGrade.A2.name,
            writing_ability=LanguageKnowledgeGrade.B1.name,
            certificate=[uuid.uuid4()],
        )
        fr_language: LanguageKnowledge = LanguageKnowledgeFactory(
            language__code='FR',
            person=self.admission.candidate,
            listening_comprehension=LanguageKnowledgeGrade.B1.name,
            speaking_ability=LanguageKnowledgeGrade.B2.name,
            writing_ability=LanguageKnowledgeGrade.C1.name,
            certificate=[uuid.uuid4()],
        )
        en_language: LanguageKnowledge = LanguageKnowledgeFactory(
            language__code='EN',
            person=self.admission.candidate,
            listening_comprehension=LanguageKnowledgeGrade.C1.name,
            speaking_ability=LanguageKnowledgeGrade.C2.name,
            writing_ability=LanguageKnowledgeGrade.A1.name,
            certificate=[uuid.uuid4()],
        )
        other_language: LanguageKnowledge = LanguageKnowledgeFactory(language__code='DE')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        knowledge: List[ConnaissanceLangueDTO] = response.context['connaissances_langues']
        self.assertEqual(len(knowledge), 3)

        self.assertEqual(knowledge[0].langue, en_language.language.code)
        self.assertEqual(knowledge[0].nom_langue_fr, en_language.language.name)
        self.assertEqual(knowledge[0].nom_langue_en, en_language.language.name_en)
        self.assertEqual(knowledge[0].comprehension_orale, en_language.listening_comprehension)
        self.assertEqual(knowledge[0].capacite_orale, en_language.speaking_ability)
        self.assertEqual(knowledge[0].capacite_ecriture, en_language.writing_ability)
        self.assertEqual(knowledge[0].certificat, en_language.certificate)

        self.assertEqual(knowledge[1].langue, fr_language.language.code)
        self.assertEqual(knowledge[1].nom_langue_fr, fr_language.language.name)
        self.assertEqual(knowledge[1].nom_langue_en, fr_language.language.name_en)
        self.assertEqual(knowledge[1].comprehension_orale, fr_language.listening_comprehension)
        self.assertEqual(knowledge[1].capacite_orale, fr_language.speaking_ability)
        self.assertEqual(knowledge[1].capacite_ecriture, fr_language.writing_ability)
        self.assertEqual(knowledge[1].certificat, fr_language.certificate)

        self.assertEqual(knowledge[2].langue, nl_language.language.code)
        self.assertEqual(knowledge[2].nom_langue_fr, nl_language.language.name)
        self.assertEqual(knowledge[2].nom_langue_en, nl_language.language.name_en)
        self.assertEqual(knowledge[2].comprehension_orale, nl_language.listening_comprehension)
        self.assertEqual(knowledge[2].capacite_orale, nl_language.speaking_ability)
        self.assertEqual(knowledge[2].capacite_ecriture, nl_language.writing_ability)
        self.assertEqual(knowledge[2].certificat, nl_language.certificate)
