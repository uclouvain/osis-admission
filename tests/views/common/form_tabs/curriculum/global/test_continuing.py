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
import uuid
from unittest.mock import patch

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from rest_framework import status

from admission.models import ContinuingEducationAdmission
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.forms import REQUIRED_FIELD_CLASS
from admission.tests.factories.continuing_education import (
    ContinuingEducationTrainingFactory,
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
)
from admission.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from admission.tests.factories.form_item import TextAdmissionFormItemFactory, AdmissionFormItemInstantiationFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory, CandidateFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_profile import BE_ISO_CODE
from osis_profile.models import EducationalExperience, EducationalExperienceYear
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2022-01-01')
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class AdmissionCurriculumGlobalFormViewForContinuingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]

        cls.entity = EntityVersionFactory().entity
        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE, name='Belgique', name_en='Belgium')
        cls.foreign_country = CountryFactory(iso_code=FR_ISO_CODE, name='France', name_en='France')

        cls.training_without_equivalence_or_curriculum = ContinuingEducationTrainingFactory(
            education_group_type__name=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
            management_entity=cls.entity,
            academic_year=cls.academic_years[1],
        )

        cls.training_without_equivalence_or_curriculum.specificiufcinformations.registration_required = False
        cls.training_without_equivalence_or_curriculum.specificiufcinformations.save()

        cls.training_with_equivalence_and_curriculum = ContinuingEducationTrainingFactory(
            education_group_type__name=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
            management_entity=cls.entity,
            academic_year=cls.academic_years[1],
        )

        cls.text_question_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(),
            academic_year=cls.academic_years[1],
            tab=Onglets.CURRICULUM.name,
            required=True,
        )

        cls.text_question_uuid = str(cls.text_question_instantiation.form_item.uuid)
        cls.other_question_uuid = str(uuid.uuid4())

        cls.candidate = CandidateFactory(
            person__graduated_from_high_school=GotDiploma.YES.name,
            person__graduated_from_high_school_year=cls.academic_years[1],
        ).person

        cls.educational_experience: EducationalExperience = EducationalExperienceFactory(
            person=cls.candidate,
            obtained_diploma=True,
            country=cls.foreign_country,
        )

        cls.educational_experience_year: EducationalExperienceYear = EducationalExperienceYearFactory(
            educational_experience=cls.educational_experience,
            academic_year=cls.academic_years[1],
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.entity).person.user

    def setUp(self):
        # Mock documents
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'size': 1, 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: ['550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'] if value else []
        self.addCleanup(patcher.stop)

        patcher = patch(
            'osis_document.api.utils.get_several_remote_metadata',
            side_effect=lambda tokens, *args, **kwargs: {
                token: {'name': 'test.pdf', 'size': 1, 'mimetype': PDF_MIME_TYPE} for token in tokens
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.continuing_admission_with_attachments: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training=self.training_with_equivalence_and_curriculum,
            candidate=self.candidate,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            specific_question_answers={
                self.text_question_uuid: 'My first answer',
                self.other_question_uuid: 'My other answer',
            },
        )

        self.continuing_admission_without_attachments: ContinuingEducationAdmission = (
            ContinuingEducationAdmissionFactory(
                training=self.training_without_equivalence_or_curriculum,
                candidate=self.candidate,
                status=ChoixStatutPropositionContinue.CONFIRMEE.name,
                specific_question_answers={
                    self.text_question_uuid: 'My first answer',
                    self.other_question_uuid: 'My other answer',
                },
            )
        )

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.continuing_admission_with_attachments,
            educationalexperience=self.educational_experience,
        )

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.continuing_admission_without_attachments,
            educationalexperience=self.educational_experience,
        )

        # Urls
        self.form_url_with_attachments = resolve_url(
            'admission:continuing-education:update:curriculum',
            uuid=self.continuing_admission_with_attachments.uuid,
        )

        self.form_url_without_attachments = resolve_url(
            'admission:continuing-education:update:curriculum',
            uuid=self.continuing_admission_without_attachments.uuid,
        )

    def test_update_global_curriculum_is_allowed_for_fac_users(self):
        program_manager_user = ProgramManagerRoleFactory(
            education_group=self.continuing_admission_with_attachments.training.education_group,
        ).person.user

        self.client.force_login(program_manager_user)
        response = self.client.get(self.form_url_with_attachments)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_education_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url_with_attachments)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        # With attachments
        response = self.client.get(self.form_url_with_attachments)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(len(form.fields['reponses_questions_specifiques'].fields), 1)

        self.assertIn('curriculum', form.fields)
        self.assertIn('equivalence_diplome', form.fields)
        self.assertNotIn(REQUIRED_FIELD_CLASS, form.fields['curriculum'].widget.attrs.get('class', ''))

        # Without attachments
        response = self.client.get(self.form_url_without_attachments)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(len(form.fields['reponses_questions_specifiques'].fields), 1)
        self.assertNotIn('curriculum', form.fields)
        self.assertNotIn('equivalence_diplome', form.fields)

    def test_submit_invalid_data(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(self.form_url_without_attachments, data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn('reponses_questions_specifiques', form.errors)
        self.assertEqual(
            len(getattr(form.fields['reponses_questions_specifiques'].fields[0], 'errors', [])),
            1,
        )

    def test_submit_valid_data(self):
        self.client.force_login(self.sic_manager_user)

        data = {
            'reponses_questions_specifiques_0': 'My new answer',
            'curriculum_0': 'curriculum-token',
            'equivalence_diplome_0': 'equivalence-token',
        }

        # Without attachments
        response = self.client.post(self.form_url_without_attachments, data=data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.continuing_admission_without_attachments.refresh_from_db()

        self.assertEqual(
            self.continuing_admission_without_attachments.specific_question_answers,
            {
                self.other_question_uuid: 'My other answer',
                self.text_question_uuid: 'My new answer',
            },
        )
        self.assertEqual(self.continuing_admission_without_attachments.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.continuing_admission_without_attachments.curriculum, [])
        self.assertEqual(self.continuing_admission_without_attachments.diploma_equivalence, [])

        # With attachments
        response = self.client.post(self.form_url_with_attachments, data=data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.continuing_admission_with_attachments.refresh_from_db()

        self.assertEqual(
            self.continuing_admission_with_attachments.specific_question_answers,
            {
                self.other_question_uuid: 'My other answer',
                self.text_question_uuid: 'My new answer',
            },
        )
        self.assertEqual(self.continuing_admission_with_attachments.last_update_author, self.sic_manager_user.person)
        self.assertNotEqual(self.continuing_admission_with_attachments.curriculum, [])
        self.assertNotEqual(self.continuing_admission_with_attachments.diploma_equivalence, [])
