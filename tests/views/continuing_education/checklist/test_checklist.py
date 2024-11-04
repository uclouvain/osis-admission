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
from typing import Dict, List

import mock
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.models import ContinuingEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
    ContinuingEducationTrainingFactory,
)
from admission.tests.factories.curriculum import AdmissionEducationalValuatedExperiencesFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from osis_profile.models import EducationalExperience


class ChecklistViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.training = ContinuingEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.MASTER_MA_120.name,
        )
        cls.training.specificiufcinformations.registration_required = True
        cls.training.specificiufcinformations.save()

        cls.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(
                country_of_citizenship__iso_code='BE',
                country_of_citizenship__european_union=True,
                id_card_number='123456789',
                passport_number='',
                language=settings.LANGUAGE_CODE_FR,
            ),
            submitted=True,
        )
        cls.candidate = cls.continuing_admission.candidate

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user

        cls.file_metadata = {
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'explicit_name': 'My file name',
            'author': cls.sic_manager_user.person.global_id,
            'size': 1,
        }

    def setUp(self) -> None:
        patcher = mock.patch('admission.templatetags.admission.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.templatetags.admission.get_remote_metadata', return_value=self.file_metadata)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_metadata', return_value=self.file_metadata)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {token: self.file_metadata for token in tokens}
        self.addCleanup(patcher.stop)

    def test_get(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:continuing-education:checklist',
            uuid=self.continuing_admission.uuid,
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, self.candidate.first_name)
        self.assertContains(response, self.candidate.last_name)

        candidate_experiences = EducationalExperience.objects.filter(
            person=self.candidate,
        )

        self.assertEqual(len(candidate_experiences), 1)

        candidate_experiences[0].obtained_diploma = True
        candidate_experiences[0].save()

        documents: Dict[str, List[EmplacementDocumentDTO]] = response.context['documents']

        self.assertIn('decision', documents)
        self.assertIn('fiche_etudiant', documents)

        self.assertEqual(documents['decision'], documents['fiche_etudiant'])

        documents_identifiers = [document.identifiant for document in documents['decision']]

        self.assertCountEqual(
            documents_identifiers,
            [
                'IDENTIFICATION.CARTE_IDENTITE',
                'CURRICULUM.CURRICULUM',
            ],
        )

        # Valuation but by another admission -> don't retrieve the related documents
        educational_valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=ContinuingEducationAdmissionFactory(candidate=self.candidate),
            educationalexperience=candidate_experiences[0],
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        documents: Dict[str, List[EmplacementDocumentDTO]] = response.context['documents']

        self.assertIn('decision', documents)
        self.assertIn('fiche_etudiant', documents)

        self.assertEqual(documents['decision'], documents['fiche_etudiant'])

        documents_identifiers = [document.identifiant for document in documents['decision']]

        self.assertCountEqual(
            documents_identifiers,
            [
                'IDENTIFICATION.CARTE_IDENTITE',
                'CURRICULUM.CURRICULUM',
            ],
        )

        # Valuation by the current admission -> retrieve the related documents
        educational_valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.continuing_admission,
            educationalexperience=candidate_experiences[0],
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        documents: Dict[str, List[EmplacementDocumentDTO]] = response.context['documents']

        self.assertIn('decision', documents)
        self.assertIn('fiche_etudiant', documents)

        self.assertEqual(documents['decision'], documents['fiche_etudiant'])

        documents_identifiers = [document.identifiant for document in documents['decision']]

        self.assertCountEqual(
            documents_identifiers,
            [
                'IDENTIFICATION.CARTE_IDENTITE',
                'CURRICULUM.CURRICULUM',
                *[f'CURRICULUM.{experience.uuid}.DIPLOME' for experience in candidate_experiences],
            ],
        )
