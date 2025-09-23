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
import itertools
import factory

import mock
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import ENTITY_CDE
from admission.ddd.admission.shared_kernel.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    PoursuiteDeCycle,
    OngletsChecklist,
)
from admission.tests.factories.curriculum import (
    EducationalExperienceYearFactory,
    EducationalExperienceFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
    AdmissionEducationalValuatedExperiencesFactory,
)
from admission.tests.factories.form_item import AdmissionFormItemFactory
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.entity import EntityWithVersionFactory
from infrastructure.financabilite.domain.service.financabilite import PASS_ET_LAS_LABEL
from osis_profile.models.enums.curriculum import Result


class ChecklistViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.MASTER_MA_120.name,
        )

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

        patcher = mock.patch('osis_document_components.services.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document_components.services.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document_components.services.get_remote_metadata', return_value=self.file_metadata)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document_components.services.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {token: self.file_metadata for token in tokens}
        self.addCleanup(patcher.stop)

        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            specific_question_answers={str(AdmissionFormItemFactory(internal_label=PASS_ET_LAS_LABEL).uuid): 0},
            submitted_at=factory.LazyAttribute(lambda obj: datetime.datetime(obj.determined_academic_year.year, 1, 1)),
        )
        self.candidate = self.general_admission.candidate

    def test_get(self):
        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:checklist',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, self.candidate.first_name)
        self.assertContains(response, self.candidate.last_name)
        self.assertContains(response, self.candidate.birth_place)
        self.assertContains(response, self.candidate.national_number)

        self.assertNotContains(response, 'Poursuite de cycle')
        self.assertNotContains(response, f'{self.training.acronym}-1')
        self.assertContains(response, self.training.acronym)
        self.assertContains(response, self.training.title)

    def test_get_only_valuated_experiences(self):
        self.client.force_login(user=self.sic_manager_user)

        educational_experience = self.candidate.educationalexperience_set.first()
        non_educational_experience = self.candidate.professionalexperience_set.first()

        educational_experience_uuid_str = str(educational_experience.uuid)
        non_educational_experience_uuid_str = str(non_educational_experience.uuid)

        secondary_studies_child_identifier = f'parcours_anterieur__{OngletsDemande.ETUDES_SECONDAIRES.name}'
        educational_experience_child_identifier = f'parcours_anterieur__{educational_experience_uuid_str}'
        non_educational_experience_child_identifier = f'parcours_anterieur__{non_educational_experience_uuid_str}'

        url = resolve_url('admission:general-education:checklist', uuid=self.general_admission.uuid)

        # No curriculum valuated experiences
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        past_experiences = [
            experience['extra']['identifiant']
            for experience in response.context['original_admission'].checklist['current']['parcours_anterieur'][
                'enfants'
            ]
        ]

        documents = response.context['documents']

        # Experiences
        self.assertIn(OngletsDemande.ETUDES_SECONDAIRES.name, past_experiences)
        self.assertNotIn(educational_experience_uuid_str, past_experiences)
        self.assertNotIn(non_educational_experience_uuid_str, past_experiences)
        self.assertEqual(response.context['last_valuated_admission_by_experience_uuid'], {})

        # Documents
        self.assertIn(secondary_studies_child_identifier, documents)
        self.assertNotIn(educational_experience_child_identifier, documents)
        self.assertNotIn(non_educational_experience_child_identifier, documents)

        # Two valuated experiences but by another admission -> we retrieve the experiences and their documents
        other_admission = GeneralEducationAdmissionFactory(
            candidate=self.general_admission.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        educational_valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=other_admission,
            educationalexperience=educational_experience,
        )

        non_educational_valuation = AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=other_admission,
            professionalexperience=non_educational_experience,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        past_experiences = [
            experience['extra']['identifiant']
            for experience in response.context['original_admission'].checklist['current']['parcours_anterieur'][
                'enfants'
            ]
        ]

        documents = response.context['documents']

        # Experiences
        self.assertIn(OngletsDemande.ETUDES_SECONDAIRES.name, past_experiences)
        self.assertIn(educational_experience_uuid_str, past_experiences)
        self.assertIn(non_educational_experience_uuid_str, past_experiences)

        mapping_valuated_admission_experience = response.context['last_valuated_admission_by_experience_uuid']
        self.assertIsNotNone(mapping_valuated_admission_experience.get(educational_experience_uuid_str))
        self.assertEqual(
            mapping_valuated_admission_experience[educational_experience_uuid_str].uuid,
            other_admission.uuid,
        )
        self.assertIsNotNone(mapping_valuated_admission_experience.get(non_educational_experience_uuid_str))
        self.assertEqual(
            mapping_valuated_admission_experience[non_educational_experience_uuid_str].uuid,
            other_admission.uuid,
        )

        # Documents
        self.assertIn(secondary_studies_child_identifier, documents)
        self.assertIn(educational_experience_child_identifier, documents)
        self.assertIn(non_educational_experience_child_identifier, documents)
        cv_experiences_documents_identifiers = {
            doc.identifiant
            for doc in itertools.chain(
                documents[educational_experience_child_identifier],
                documents[non_educational_experience_child_identifier],
            )
        }
        secondary_studies_documents_identifiers = set(
            doc.identifiant for doc in documents[secondary_studies_child_identifier]
        )
        self.assertCountEqual(response.context['read_only_documents'], cv_experiences_documents_identifiers)

        past_experiences_documents = set(doc.identifiant for doc in documents[OngletsChecklist.parcours_anterieur.name])
        financeability_documents = set(doc.identifiant for doc in documents[OngletsChecklist.financabilite.name])

        self.assertTrue(cv_experiences_documents_identifiers <= past_experiences_documents)
        self.assertTrue(cv_experiences_documents_identifiers <= financeability_documents)
        self.assertTrue(secondary_studies_documents_identifiers <= past_experiences_documents)

        # Two valuated experiences by the current admission -> we retrieve the experiences and their documents
        educational_valuation.baseadmission = self.general_admission
        educational_valuation.save(update_fields=['baseadmission'])

        non_educational_valuation.baseadmission = self.general_admission
        non_educational_valuation.save(update_fields=['baseadmission'])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        past_experiences = [
            experience['extra']['identifiant']
            for experience in response.context['original_admission'].checklist['current']['parcours_anterieur'][
                'enfants'
            ]
        ]

        documents = response.context['documents']

        # Experiences
        self.assertIn(OngletsDemande.ETUDES_SECONDAIRES.name, past_experiences)
        self.assertIn(educational_experience_uuid_str, past_experiences)
        self.assertIn(non_educational_experience_uuid_str, past_experiences)
        self.assertEqual(response.context['last_valuated_admission_by_experience_uuid'], {})

        # Documents
        self.assertIn(secondary_studies_child_identifier, documents)
        self.assertIn(educational_experience_child_identifier, documents)
        self.assertIn(non_educational_experience_child_identifier, documents)
        cv_experiences_documents_identifiers = {
            doc.identifiant
            for doc in itertools.chain(
                documents[educational_experience_child_identifier],
                documents[non_educational_experience_child_identifier],
            )
        }
        secondary_studies_documents_identifiers = set(
            doc.identifiant for doc in documents[secondary_studies_child_identifier]
        )

        self.assertEqual(response.context['read_only_documents'], [])

        past_experiences_documents = set(doc.identifiant for doc in documents[OngletsChecklist.parcours_anterieur.name])
        financeability_documents = set(doc.identifiant for doc in documents[OngletsChecklist.financabilite.name])

        self.assertTrue(cv_experiences_documents_identifiers <= past_experiences_documents)
        self.assertTrue(cv_experiences_documents_identifiers <= financeability_documents)
        self.assertTrue(secondary_studies_documents_identifiers <= past_experiences_documents)

    def test_poursuite_de_cycle_no(self):
        self.training.education_group_type = EducationGroupTypeFactory(name=TrainingType.BACHELOR.name)
        self.training.save(update_fields=['education_group_type'])
        EducationalExperienceYearFactory(
            result=Result.SUCCESS.name,
            educational_experience=EducationalExperienceFactory(person=self.candidate),
        )
        self.general_admission.cycle_pursuit = PoursuiteDeCycle.NO.name
        self.general_admission.save(update_fields=['cycle_pursuit'])

        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:checklist',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Poursuite de cycle')
        self.assertContains(response, f'{self.training.acronym}-1')

    def test_poursuite_de_cycle_yes(self):
        self.training.education_group_type = EducationGroupTypeFactory(name=TrainingType.BACHELOR.name)
        self.training.save(update_fields=['education_group_type'])
        EducationalExperienceYearFactory(
            result=Result.SUCCESS.name,
            educational_experience=EducationalExperienceFactory(person=self.candidate),
        )
        self.general_admission.cycle_pursuit = PoursuiteDeCycle.YES.name
        self.general_admission.save(update_fields=['cycle_pursuit'])

        self.client.force_login(user=self.sic_manager_user)

        url = resolve_url(
            'admission:general-education:checklist',
            uuid=self.general_admission.uuid,
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Poursuite de cycle')
        self.assertNotContains(response, f'{self.training.acronym}-1')
