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
from unittest import mock

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy
from rest_framework import status

from admission.models import EPCInjection as AdmissionEPCInjection, ContinuingEducationAdmission
from admission.models.epc_injection import EPCInjectionType, EPCInjectionStatus as AdmissionEPCInjectionStatus
from admission.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.form_item import TextAdmissionFormItemFactory, AdmissionFormItemInstantiationFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from admission.tests.factories.secondary_studies import (
    BelgianHighSchoolDiplomaFactory,
    ForeignHighSchoolDiplomaFactory,
    HighSchoolDiplomaAlternativeFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.choice_field import BLANK_CHOICE_DISPLAY
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.academic_year import AcademicYear
from base.models.enums.community import CommunityEnum
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import (
    Master120TrainingFactory,
    EducationGroupYearBachelorFactory,
    ContinuingEducationTrainingFactory,
)
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, HighSchoolDiplomaAlternative
from osis_profile.models.enums.education import (
    EducationalType,
    ForeignDiplomaTypes,
    Equivalence,
    HighSchoolDiplomaTypes,
)
from osis_profile.models.epc_injection import (
    EPCInjection as CurriculumEPCInjection,
    ExperienceType,
    EPCInjectionStatus as CurriculumEPCInjectionStatus,
)
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.domain import DomainFactory
from reference.tests.factories.language import LanguageFactory, FrenchLanguageFactory


@freezegun.freeze_time("2022-01-01")
class AdmissionEducationFormViewForMasterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.training = Master120TrainingFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
        ).person.user

    def setUp(self):
        # Mocked data
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate__graduated_from_high_school=GotDiploma.THIS_YEAR.name,
            candidate__graduated_from_high_school_year=self.academic_years[1],
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Url
        self.form_url = resolve_url('admission:general-education:update:education', uuid=self.general_admission.uuid)

        # Mock osis document api
        patcher = mock.patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: value

    def test_update_education_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_education_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_education_is_not_allowed_for_injected_experiences(self):
        self.client.force_login(self.sic_manager_user)

        # The experience has been injected from the curriculum
        cv_injection = CurriculumEPCInjection.objects.create(
            person=self.general_admission.candidate,
            type_experience=ExperienceType.HIGH_SCHOOL.name,
            status=CurriculumEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        cv_injection.delete()

        # The experience has been injected from another admission
        other_admission = GeneralEducationAdmissionFactory(candidate=self.general_admission.candidate)

        other_admission_injection = AdmissionEPCInjection.objects.create(
            admission=other_admission,
            type=EPCInjectionType.DEMANDE.name,
            status=AdmissionEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        other_admission.delete()

        # The current admission has been injected
        admission_injection = AdmissionEPCInjection.objects.create(
            admission=self.general_admission,
            type=EPCInjectionType.DEMANDE.name,
            status=AdmissionEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        # Graduated from high school
        self.assertEqual(form['graduated_from_high_school'].value(), GotDiploma.THIS_YEAR.name)
        self.assertEqual(
            form.fields['graduated_from_high_school'].choices,
            [
                (GotDiploma.YES.name, GotDiploma.YES.value),
                (
                    GotDiploma.THIS_YEAR.name,
                    gettext_lazy('I will be graduating from secondary school during the %s academic year')
                    % '2021-2022',
                ),
                (GotDiploma.NO.name, GotDiploma.NO.value),
            ],
        )

        # Graduated from high school year
        self.assertEqual(form['graduated_from_high_school_year'].value(), 2021)

        all_past_academic_years = AcademicYear.objects.filter(year__lte=2021).order_by('-year')

        academic_year_choices = [('', BLANK_CHOICE_DISPLAY)] + [
            (academic_year.year, f'{academic_year.year}-{academic_year.year + 1}')
            for academic_year in all_past_academic_years
        ]

        self.assertEqual(
            [(c[0], c[1]) for c in form.fields['graduated_from_high_school_year'].choices],
            academic_year_choices,
        )

    def test_submit_invalid_data(self):
        self.client.force_login(self.sic_manager_user)

        # No data
        response = self.client.post(self.form_url, data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('graduated_from_high_school', []))

        # Has a diploma
        response = self.client.post(self.form_url, data={'graduated_from_high_school': GotDiploma.YES.name})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('graduated_from_high_school_year', []))

    def test_submit_valid_data_when_the_candidate_has_a_diploma_without_existing_ones(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertNotIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.general_admission.requested_documents,
        )

    def test_submit_valid_data_when_the_candidate_has_a_diploma_with_existing_belgian_diploma(self):
        self.client.force_login(self.sic_manager_user)

        belgian_high_school_diploma = BelgianHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            academic_graduation_year=self.academic_years[1],
        )

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        self.assertTrue(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        belgian_high_school_diploma.refresh_from_db()

        self.assertEqual(belgian_high_school_diploma.academic_graduation_year, self.academic_years[0])

    def test_submit_valid_data_when_the_candidate_has_a_diploma_with_existing_foreign_diploma(self):
        self.client.force_login(self.sic_manager_user)

        # Previous existing foreign high school diploma before the request
        foreign_high_school_diploma = ForeignHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            academic_graduation_year=self.academic_years[1],
        )

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertTrue(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        foreign_high_school_diploma.refresh_from_db()

        self.assertEqual(foreign_high_school_diploma.academic_graduation_year, self.academic_years[0])

    def test_submit_valid_data_when_the_candidate_has_a_diploma_with_existing_alternative_diploma_and_redirect(self):
        self.client.force_login(self.sic_manager_user)

        admission_url = resolve_url('admission')
        expected_url = f'{admission_url}#custom_hash'

        high_school_diploma_alternative = HighSchoolDiplomaAlternativeFactory(person=self.general_admission.candidate)

        response = self.client.post(
            f'{self.form_url}?next={admission_url}&next_hash_url=custom_hash',
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertRedirects(response=response, fetch_redirect_response=False, expected_url=expected_url)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

    def test_submit_valid_data_when_the_candidate_will_have_a_diploma_without_existing_ones(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

    def test_submit_valid_data_when_the_candidate_will_have_a_diploma_with_existing_belgian_diploma(self):
        self.client.force_login(self.sic_manager_user)

        belgian_high_school_diploma = BelgianHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            academic_graduation_year=self.academic_years[0],
        )

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.THIS_YEAR.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.THIS_YEAR.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[1])

        self.assertTrue(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        belgian_high_school_diploma.refresh_from_db()

        self.assertEqual(belgian_high_school_diploma.academic_graduation_year, self.academic_years[1])

    def test_submit_valid_data_when_the_candidate_will_have_a_diploma_with_existing_foreign_diploma(self):
        self.client.force_login(self.sic_manager_user)

        # Previous existing foreign high school diploma before the request
        foreign_high_school_diploma = ForeignHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            academic_graduation_year=self.academic_years[0],
        )

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.THIS_YEAR.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.THIS_YEAR.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[1])

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertTrue(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        foreign_high_school_diploma.refresh_from_db()

        self.assertEqual(foreign_high_school_diploma.academic_graduation_year, self.academic_years[1])

    def test_submit_valid_data_when_the_candidate_will_have_a_diploma_with_existing_alternative_diploma(self):
        self.client.force_login(self.sic_manager_user)

        high_school_diploma_alternative = HighSchoolDiplomaAlternativeFactory(person=self.general_admission.candidate)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.THIS_YEAR.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.THIS_YEAR.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[1])

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

    def test_submit_valid_data_when_the_candidate_has_no_diploma_without_existing_ones(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.NO.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, None)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

    def test_submit_answers_to_specific_questions(self):
        self.client.force_login(self.sic_manager_user)

        text_question = TextAdmissionFormItemFactory()
        text_question_uuid = str(text_question.uuid)

        text_question_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=text_question,
            academic_year=self.training.academic_year,
            tab=Onglets.CHOIX_FORMATION.name,
            required=True,
        )

        self.general_admission.specific_question_answers[text_question_uuid] = 'My first answer'
        self.general_admission.save(update_fields=['specific_question_answers'])

        # No specific question in the form
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.specific_question_answers.get(text_question_uuid), 'My first answer')
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # One specific question in the form
        text_question_instantiation.tab = Onglets.ETUDES_SECONDAIRES.name
        text_question_instantiation.save(update_fields=['tab'])

        # But no answer
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn('specific_question_answers', form.errors)

        self.assertEqual(
            len(getattr(form.fields['specific_question_answers'].fields[0], 'errors', [])),
            1,
        )

        # And one answer
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'specific_question_answers_0': 'My second answer',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.specific_question_answers.get(text_question_uuid), 'My second answer')

    def test_submit_valid_data_when_the_candidate_has_no_diploma_with_existing_belgian_diploma(self):
        self.client.force_login(self.sic_manager_user)

        BelgianHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            academic_graduation_year=self.academic_years[0],
        )

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.NO.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, None)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

    def test_submit_valid_data_when_the_candidate_has_no_diploma_with_existing_foreign_diploma(self):
        self.client.force_login(self.sic_manager_user)

        # Previous existing foreign high school diploma before the request
        ForeignHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            academic_graduation_year=self.academic_years[0],
        )

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.NO.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, None)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

    def test_submit_valid_data_when_the_candidate_has_no_diploma_with_existing_alternative_diploma(self):
        self.client.force_login(self.sic_manager_user)

        HighSchoolDiplomaAlternativeFactory(person=self.general_admission.candidate)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.NO.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, None)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertTrue(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())


@freezegun.freeze_time("2022-01-01")
class AdmissionEducationFormViewForContinuingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.training = ContinuingEducationTrainingFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
        )

        cls.specific_question = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(),
            tab=OngletsDemande.ETUDES_SECONDAIRES.name,
            academic_year=cls.training.academic_year,
        )
        cls.specific_question_uuid = str(cls.specific_question.form_item.uuid)

        cls.other_specific_question = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(),
            tab=OngletsDemande.CURRICULUM.name,
        )
        cls.other_specific_question_uuid = str(cls.other_specific_question.form_item.uuid)

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
        ).person.user

    def setUp(self):
        # Mocked data
        self.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training=self.training,
            candidate__graduated_from_high_school=GotDiploma.THIS_YEAR.name,
            candidate__graduated_from_high_school_year=self.academic_years[1],
            candidate__id_photo=[],
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            specific_question_answers={
                self.other_specific_question_uuid: 'My other answer',
            },
        )

        # Url
        self.form_url = resolve_url(
            'admission:continuing-education:update:education',
            uuid=self.continuing_admission.uuid,
        )

        # Mock osis document api
        patcher = mock.patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: value

    def test_update_education_is_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_education_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_submit_valid_data(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'specific_question_answers_0': 'My answer',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check saved data
        self.continuing_admission.refresh_from_db()
        candidate = self.continuing_admission.candidate

        self.assertEqual(candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(candidate.graduated_from_high_school_year, self.academic_years[0])

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=candidate).exists())

        self.assertEqual(
            self.continuing_admission.specific_question_answers,
            {
                self.specific_question_uuid: 'My answer',
                self.other_specific_question_uuid: 'My other answer',
            },
        )

        # Check additional updates
        self.assertEqual(self.continuing_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.continuing_admission.last_update_author, self.sic_manager_user.person)
        self.assertNotIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.continuing_admission.requested_documents,
        )


@freezegun.freeze_time("2022-01-01")
class AdmissionEducationFormViewForBachelorTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.training = EducationGroupYearBachelorFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
        )

        cls.files_uuids = {
            name_field: uuid.uuid4()
            for name_field in [
                'high_school_diploma',
                'first_cycle_admission_exam',
                'high_school_transcript',
                'high_school_transcript_translation',
                'high_school_diploma_translation',
                'final_equivalence_decision_not_ue',
                'final_equivalence_decision_ue',
                'equivalence_decision_proof',
            ]
        }

        cls.french_linguistic_regime = FrenchLanguageFactory()
        cls.greek_linguistic_regime = LanguageFactory(code='EL')

        cls.france_country = CountryFactory(iso_code="FR", european_union=True)
        cls.us_country = CountryFactory(iso_code="US", european_union=False)

        cls.first_institute = OrganizationFactory(
            community=CommunityEnum.FRENCH_SPEAKING.name,
            establishment_type=EstablishmentTypeEnum.HIGH_SCHOOL.name,
        )
        cls.second_institute = OrganizationFactory(
            community=CommunityEnum.FRENCH_SPEAKING.name,
            establishment_type=EstablishmentTypeEnum.HIGH_SCHOOL.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user

    def setUp(self):
        # Mocked data
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            candidate__graduated_from_high_school=GotDiploma.THIS_YEAR.name,
            candidate__graduated_from_high_school_year=self.academic_years[1],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Url
        self.form_url = resolve_url('admission:general-education:update:education', uuid=self.general_admission.uuid)

        # Mock osis document api
        patcher = mock.patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: value

    def test_update_education_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_education_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_education_is_not_allowed_for_injected_experiences(self):
        self.client.force_login(self.sic_manager_user)

        # The experience has been injected from the curriculum
        cv_injection = CurriculumEPCInjection.objects.create(
            person=self.general_admission.candidate,
            type_experience=ExperienceType.HIGH_SCHOOL.name,
            status=CurriculumEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        cv_injection.delete()

        # The admission has been injected
        admission_injection = AdmissionEPCInjection.objects.create(
            admission=self.general_admission,
            type=EPCInjectionType.DEMANDE.name,
            status=AdmissionEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        admission_injection.delete()

        # The experience come from EPC
        belgian_diploma = BelgianHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            external_id='EP1-1',
        )

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Reset the experience
        belgian_diploma.external_id = ''
        belgian_diploma.save(update_fields=['external_id'])

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_form_initialization_without_existing_diploma(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # > Main form
        main_form = response.context['main_form']

        # Graduated from high school
        self.assertEqual(main_form['graduated_from_high_school'].value(), GotDiploma.THIS_YEAR.name)
        self.assertEqual(
            main_form.fields['graduated_from_high_school'].choices,
            [
                (GotDiploma.YES.name, GotDiploma.YES.value),
                (
                    GotDiploma.THIS_YEAR.name,
                    gettext_lazy('I will be graduating from secondary school during the %s academic year')
                    % '2021-2022',
                ),
                (GotDiploma.NO.name, GotDiploma.NO.value),
            ],
        )

        # Graduated from high school year
        self.assertEqual(main_form['graduated_from_high_school_year'].value(), 2021)

        all_past_academic_years = AcademicYear.objects.filter(year__lte=2021).order_by('-year')

        academic_year_choices = [('', BLANK_CHOICE_DISPLAY)] + [
            (academic_year.year, f'{academic_year.year}-{academic_year.year + 1}')
            for academic_year in all_past_academic_years
        ]

        self.assertEqual(
            [(c[0], c[1]) for c in main_form.fields['graduated_from_high_school_year'].choices],
            academic_year_choices,
        )

        # High school diploma
        self.assertEqual(main_form['high_school_diploma'].value(), [])

        # First cycle admission exam
        self.assertEqual(main_form['first_cycle_admission_exam'].value(), [])

        # > Belgian diploma form
        belgian_diploma_form = response.context['belgian_diploma_form']

        # Community
        self.assertEqual(belgian_diploma_form['community'].value(), None)

        # Educational type
        self.assertEqual(belgian_diploma_form['educational_type'].value(), None)

        # Has other educational type
        self.assertEqual(belgian_diploma_form['has_other_educational_type'].value(), False)

        # Educational other
        self.assertEqual(belgian_diploma_form['educational_other'].value(), None)

        # Institute
        self.assertEqual(belgian_diploma_form['institute'].value(), None)

        # Other institute
        self.assertEqual(belgian_diploma_form['other_institute'].value(), False)

        # Other institute name
        self.assertEqual(belgian_diploma_form['other_institute_name'].value(), None)

        # Other institute address
        self.assertEqual(belgian_diploma_form['other_institute_address'].value(), None)

        # > Foreign diploma form
        foreign_diploma_form = response.context['foreign_diploma_form']

        # Foreign diploma type
        self.assertEqual(foreign_diploma_form['foreign_diploma_type'].value(), None)

        # Equivalence
        self.assertEqual(foreign_diploma_form['equivalence'].value(), None)

        # Linguistic regime
        self.assertEqual(foreign_diploma_form['linguistic_regime'].value(), None)

        # Other linguistic regime
        self.assertEqual(foreign_diploma_form['other_linguistic_regime'].value(), None)

        # Country
        self.assertEqual(foreign_diploma_form['country'].value(), None)

        # High school transcript
        self.assertEqual(foreign_diploma_form['high_school_transcript'].value(), [])

        # High school transcript translation
        self.assertEqual(foreign_diploma_form['high_school_transcript_translation'].value(), [])

        # High school diploma translation
        self.assertEqual(foreign_diploma_form['high_school_diploma_translation'].value(), [])

        # Final equivalence decision not UE
        self.assertEqual(foreign_diploma_form['final_equivalence_decision_not_ue'].value(), [])

        # Final equivalence decision UE
        self.assertEqual(foreign_diploma_form['final_equivalence_decision_ue'].value(), [])

        # Equivalence decision proof
        self.assertEqual(foreign_diploma_form['equivalence_decision_proof'].value(), [])

    def test_form_initialization_with_existing_belgian_diploma(self):
        self.client.force_login(self.sic_manager_user)

        belgian_diploma = BelgianHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            high_school_diploma=[self.files_uuids['high_school_diploma']],
            community=CommunityEnum.FRENCH_SPEAKING.name,
            educational_type=EducationalType.PROFESSIONAL_EDUCATION.name,
            educational_other='Other education',
            institute=self.first_institute,
            other_institute_name='Other institute',
            other_institute_address='Other institute address',
        )

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # > Main form
        main_form = response.context['main_form']

        # Graduated from high school
        self.assertEqual(main_form['graduated_from_high_school'].value(), GotDiploma.THIS_YEAR.name)

        # Graduated from high school year
        self.assertEqual(main_form['graduated_from_high_school_year'].value(), 2021)

        # High school diploma
        self.assertEqual(main_form['high_school_diploma'].value(), [self.files_uuids['high_school_diploma']])

        # Diploma type
        self.assertEqual(main_form['diploma_type'].value(), HighSchoolDiplomaTypes.BELGIAN.name)

        # First cycle admission exam
        self.assertEqual(main_form['first_cycle_admission_exam'].value(), [])

        # > Belgian diploma form
        belgian_diploma_form = response.context['belgian_diploma_form']

        # Community
        self.assertEqual(belgian_diploma_form['community'].value(), CommunityEnum.FRENCH_SPEAKING.name)

        # Educational type
        self.assertEqual(belgian_diploma_form['educational_type'].value(), EducationalType.PROFESSIONAL_EDUCATION.name)

        # Has other educational type
        self.assertEqual(belgian_diploma_form['has_other_educational_type'].value(), True)

        # Educational other
        self.assertEqual(belgian_diploma_form['educational_other'].value(), 'Other education')

        # Institute
        self.assertEqual(belgian_diploma_form['institute'].value(), self.first_institute.pk)

        # Other institute
        self.assertEqual(belgian_diploma_form['other_institute'].value(), True)

        # Other institute name
        self.assertEqual(belgian_diploma_form['other_institute_name'].value(), 'Other institute')

        # Other institute address
        self.assertEqual(belgian_diploma_form['other_institute_address'].value(), 'Other institute address')

        # > Foreign diploma form
        foreign_diploma_form = response.context['foreign_diploma_form']

        # Foreign diploma type
        self.assertEqual(foreign_diploma_form['foreign_diploma_type'].value(), None)

        # Equivalence
        self.assertEqual(foreign_diploma_form['equivalence'].value(), None)

        # Linguistic regime
        self.assertEqual(foreign_diploma_form['linguistic_regime'].value(), None)

        # Other linguistic regime
        self.assertEqual(foreign_diploma_form['other_linguistic_regime'].value(), None)

        # Country
        self.assertEqual(foreign_diploma_form['country'].value(), None)

        # High school transcript
        self.assertEqual(foreign_diploma_form['high_school_transcript'].value(), [])

        # High school transcript translation
        self.assertEqual(foreign_diploma_form['high_school_transcript_translation'].value(), [])

        # High school diploma translation
        self.assertEqual(foreign_diploma_form['high_school_diploma_translation'].value(), [])

        # Final equivalence decision not UE
        self.assertEqual(foreign_diploma_form['final_equivalence_decision_not_ue'].value(), [])

        # Final equivalence decision UE
        self.assertEqual(foreign_diploma_form['final_equivalence_decision_ue'].value(), [])

        # Equivalence decision proof
        self.assertEqual(foreign_diploma_form['equivalence_decision_proof'].value(), [])

    def test_form_initialization_with_existing_foreign_diploma(self):
        self.client.force_login(self.sic_manager_user)

        foreign_diploma = ForeignHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            high_school_diploma=[self.files_uuids['high_school_diploma']],
            foreign_diploma_type=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
            equivalence=Equivalence.YES.name,
            linguistic_regime=self.french_linguistic_regime,
            other_linguistic_regime='Other linguistic regime',
            country=self.france_country,
            high_school_transcript=[self.files_uuids['high_school_transcript']],
            high_school_transcript_translation=[self.files_uuids['high_school_transcript_translation']],
            high_school_diploma_translation=[self.files_uuids['high_school_diploma_translation']],
            final_equivalence_decision_not_ue=[self.files_uuids['final_equivalence_decision_not_ue']],
            final_equivalence_decision_ue=[self.files_uuids['final_equivalence_decision_ue']],
            equivalence_decision_proof=[self.files_uuids['equivalence_decision_proof']],
        )

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # > Main form
        main_form = response.context['main_form']

        # Graduated from high school
        self.assertEqual(main_form['graduated_from_high_school'].value(), GotDiploma.THIS_YEAR.name)

        # Graduated from high school year
        self.assertEqual(main_form['graduated_from_high_school_year'].value(), 2021)

        # High school diploma
        self.assertEqual(main_form['high_school_diploma'].value(), [self.files_uuids['high_school_diploma']])

        # Diploma type
        self.assertEqual(main_form['diploma_type'].value(), HighSchoolDiplomaTypes.FOREIGN.name)

        # First cycle admission exam
        self.assertEqual(main_form['first_cycle_admission_exam'].value(), [])

        # > Belgian diploma form
        belgian_diploma_form = response.context['belgian_diploma_form']

        # Community
        self.assertEqual(belgian_diploma_form['community'].value(), None)

        # Educational type
        self.assertEqual(belgian_diploma_form['educational_type'].value(), None)

        # Has other educational type
        self.assertEqual(belgian_diploma_form['has_other_educational_type'].value(), False)

        # Educational other
        self.assertEqual(belgian_diploma_form['educational_other'].value(), None)

        # Institute
        self.assertEqual(belgian_diploma_form['institute'].value(), None)

        # Other institute
        self.assertEqual(belgian_diploma_form['other_institute'].value(), False)

        # Other institute name
        self.assertEqual(belgian_diploma_form['other_institute_name'].value(), None)

        # Other institute address
        self.assertEqual(belgian_diploma_form['other_institute_address'].value(), None)

        # > Foreign diploma form
        foreign_diploma_form = response.context['foreign_diploma_form']

        # Foreign diploma type
        self.assertEqual(
            foreign_diploma_form['foreign_diploma_type'].value(),
            ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
        )

        # Equivalence
        self.assertEqual(foreign_diploma_form['equivalence'].value(), Equivalence.YES.name)

        # Linguistic regime
        self.assertEqual(foreign_diploma_form['linguistic_regime'].value(), self.french_linguistic_regime.code)

        # Other linguistic regime
        self.assertEqual(foreign_diploma_form['other_linguistic_regime'].value(), 'Other linguistic regime')

        # Country
        self.assertEqual(foreign_diploma_form['country'].value(), self.france_country.iso_code)
        self.assertEqual(
            getattr(foreign_diploma_form.fields['country'], 'is_ue_country'),
            self.france_country.european_union,
        )

        # High school transcript
        self.assertEqual(
            foreign_diploma_form['high_school_transcript'].value(),
            [self.files_uuids['high_school_transcript']],
        )

        # High school transcript translation
        self.assertEqual(
            foreign_diploma_form['high_school_transcript_translation'].value(),
            [self.files_uuids['high_school_transcript_translation']],
        )

        # High school diploma translation
        self.assertEqual(
            foreign_diploma_form['high_school_diploma_translation'].value(),
            [self.files_uuids['high_school_diploma_translation']],
        )

        # Final equivalence decision not UE
        self.assertEqual(
            foreign_diploma_form['final_equivalence_decision_not_ue'].value(),
            [self.files_uuids['final_equivalence_decision_not_ue']],
        )

        # Final equivalence decision UE
        self.assertEqual(
            foreign_diploma_form['final_equivalence_decision_ue'].value(),
            [self.files_uuids['final_equivalence_decision_ue']],
        )

        # Equivalence decision proof
        self.assertEqual(
            foreign_diploma_form['equivalence_decision_proof'].value(),
            [self.files_uuids['equivalence_decision_proof']],
        )

    def test_form_initialization_with_existing_diploma_alternative(self):
        self.client.force_login(self.sic_manager_user)

        alternative = HighSchoolDiplomaAlternativeFactory(
            person=self.general_admission.candidate,
            first_cycle_admission_exam=[self.files_uuids['first_cycle_admission_exam']],
        )

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # > Main form
        main_form = response.context['main_form']

        # Graduated from high school
        self.assertEqual(main_form['graduated_from_high_school'].value(), GotDiploma.THIS_YEAR.name)

        # Graduated from high school year
        self.assertEqual(main_form['graduated_from_high_school_year'].value(), 2021)

        # High school diploma
        self.assertEqual(main_form['high_school_diploma'].value(), [])

        # Diploma type
        self.assertEqual(main_form['diploma_type'].value(), None)

        # First cycle admission exam
        self.assertEqual(
            main_form['first_cycle_admission_exam'].value(), [self.files_uuids['first_cycle_admission_exam']]
        )

        # > Belgian diploma form
        belgian_diploma_form = response.context['belgian_diploma_form']

        # Community
        self.assertEqual(belgian_diploma_form['community'].value(), None)

        # Educational type
        self.assertEqual(belgian_diploma_form['educational_type'].value(), None)

        # Has other educational type
        self.assertEqual(belgian_diploma_form['has_other_educational_type'].value(), False)

        # Educational other
        self.assertEqual(belgian_diploma_form['educational_other'].value(), None)

        # Institute
        self.assertEqual(belgian_diploma_form['institute'].value(), None)

        # Other institute
        self.assertEqual(belgian_diploma_form['other_institute'].value(), False)

        # Other institute name
        self.assertEqual(belgian_diploma_form['other_institute_name'].value(), None)

        # Other institute address
        self.assertEqual(belgian_diploma_form['other_institute_address'].value(), None)

        # > Foreign diploma form
        foreign_diploma_form = response.context['foreign_diploma_form']

        # Foreign diploma type
        # Foreign diploma type
        self.assertEqual(foreign_diploma_form['foreign_diploma_type'].value(), None)

        # Equivalence
        self.assertEqual(foreign_diploma_form['equivalence'].value(), None)

        # Linguistic regime
        self.assertEqual(foreign_diploma_form['linguistic_regime'].value(), None)

        # Other linguistic regime
        self.assertEqual(foreign_diploma_form['other_linguistic_regime'].value(), None)

        # Country
        self.assertEqual(foreign_diploma_form['country'].value(), None)

        # High school transcript
        self.assertEqual(foreign_diploma_form['high_school_transcript'].value(), [])

        # High school transcript translation
        self.assertEqual(foreign_diploma_form['high_school_transcript_translation'].value(), [])

        # High school diploma translation
        self.assertEqual(foreign_diploma_form['high_school_diploma_translation'].value(), [])

        # Final equivalence decision not UE
        self.assertEqual(foreign_diploma_form['final_equivalence_decision_not_ue'].value(), [])

        # Final equivalence decision UE
        self.assertEqual(foreign_diploma_form['final_equivalence_decision_ue'].value(), [])

        # Equivalence decision proof
        self.assertEqual(foreign_diploma_form['equivalence_decision_proof'].value(), [])

    def test_submit_invalid_data_for_unknown_diploma(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        main_form = response.context['main_form']
        self.assertEqual(main_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, main_form.errors.get('diploma_type'))

    def test_submit_invalid_data_for_belgian_diploma(self):
        self.client.force_login(self.sic_manager_user)

        # Choose to select existing values but don't select any
        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'diploma_type': HighSchoolDiplomaTypes.BELGIAN.name,
                'belgian_diploma-community': CommunityEnum.FRENCH_SPEAKING.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Belgian diploma form
        belgian_diploma_form = response.context['belgian_diploma_form']
        self.assertEqual(belgian_diploma_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, belgian_diploma_form.errors.get('educational_type', []))
        self.assertIn(
            gettext_lazy('Please choose the institute or specify another institute'),
            belgian_diploma_form.errors.get('institute', []),
        )

        # Choose to specify other values but don't specify any
        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'diploma_type': HighSchoolDiplomaTypes.BELGIAN.name,
                'belgian_diploma-community': CommunityEnum.FRENCH_SPEAKING.name,
                'belgian_diploma-has_other_educational_type': True,
                'belgian_diploma-other_institute': True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Belgian diploma form
        belgian_diploma_form = response.context['belgian_diploma_form']
        self.assertEqual(belgian_diploma_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, belgian_diploma_form.errors.get('educational_other', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, belgian_diploma_form.errors.get('other_institute_name', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, belgian_diploma_form.errors.get('other_institute_address', []))

    def test_submit_invalid_data_for_foreign_diploma(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Foreign diploma form
        foreign_diploma_form = response.context['foreign_diploma_form']
        self.assertEqual(foreign_diploma_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, foreign_diploma_form.errors.get('foreign_diploma_type', []))
        self.assertIn(
            gettext_lazy('Please choose the language regime or specify another regime.'),
            foreign_diploma_form.errors.get('linguistic_regime', []),
        )
        self.assertIn(FIELD_REQUIRED_MESSAGE, foreign_diploma_form.errors.get('country', []))
        self.assertNotIn(FIELD_REQUIRED_MESSAGE, foreign_diploma_form.errors.get('equivalence', []))

        # Equivalence field is required for ue countries
        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
                'foreign_diploma-foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                'foreign_diploma-country': self.france_country.iso_code,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        foreign_diploma_form = response.context['foreign_diploma_form']
        self.assertEqual(foreign_diploma_form.is_valid(), False)

        self.assertIn(FIELD_REQUIRED_MESSAGE, foreign_diploma_form.errors.get('equivalence', []))
        self.assertEqual(getattr(foreign_diploma_form.fields['country'], 'is_ue_country', False), True)

        # Equivalence field is required for medical and dentistry trainings
        self.general_admission.training.main_domain = DomainFactory(code='11AB')
        self.general_admission.training.save()

        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
                'foreign_diploma-foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        foreign_diploma_form = response.context['foreign_diploma_form']

        self.assertIn(FIELD_REQUIRED_MESSAGE, foreign_diploma_form.errors.get('equivalence', []))

    def test_submit_valid_data_for_belgian_diploma_with_existing_belgian_diploma(self):
        self.client.force_login(self.sic_manager_user)

        belgian_diploma = BelgianHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            academic_graduation_year=self.academic_years[1],
            high_school_diploma=[self.files_uuids['high_school_diploma']],
            community=CommunityEnum.FRENCH_SPEAKING.name,
            educational_type=EducationalType.PROFESSIONAL_EDUCATION.name,
            educational_other='Other education',
            institute=self.first_institute,
            other_institute_name='Other institute',
            other_institute_address='Other institute address',
        )

        # Choose existing values
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'high_school_diploma_0': [self.files_uuids['high_school_diploma']],
                'diploma_type': HighSchoolDiplomaTypes.BELGIAN.name,
                'belgian_diploma-community': CommunityEnum.FRENCH_SPEAKING.name,
                'belgian_diploma-educational_type': EducationalType.PROFESSIONAL_EDUCATION.name,
                'belgian_diploma-has_other_educational_type': False,
                'belgian_diploma-educational_other': 'Other education',
                'belgian_diploma-institute': self.first_institute.pk,
                'belgian_diploma-other_institute': False,
                'belgian_diploma-other_institute_name': 'Other institute',
                'belgian_diploma-other_institute_address': 'Other institute address',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertTrue(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        belgian_diploma.refresh_from_db()

        self.assertEqual(belgian_diploma.person, self.general_admission.candidate)
        self.assertEqual(belgian_diploma.academic_graduation_year, self.academic_years[0])
        self.assertEqual(belgian_diploma.high_school_diploma, [self.files_uuids['high_school_diploma']])
        self.assertEqual(belgian_diploma.community, CommunityEnum.FRENCH_SPEAKING.name)
        self.assertEqual(belgian_diploma.educational_type, EducationalType.PROFESSIONAL_EDUCATION.name)
        self.assertEqual(belgian_diploma.educational_other, '')
        self.assertEqual(belgian_diploma.institute, self.first_institute)
        self.assertEqual(belgian_diploma.other_institute_name, '')
        self.assertEqual(belgian_diploma.other_institute_address, '')

        # Specify other values
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'high_school_diploma_0': [self.files_uuids['high_school_diploma']],
                'diploma_type': HighSchoolDiplomaTypes.BELGIAN.name,
                'belgian_diploma-community': CommunityEnum.FRENCH_SPEAKING.name,
                'belgian_diploma-educational_type': EducationalType.PROFESSIONAL_EDUCATION.name,
                'belgian_diploma-has_other_educational_type': True,
                'belgian_diploma-educational_other': 'Other education',
                'belgian_diploma-institute': self.first_institute.pk,
                'belgian_diploma-other_institute': True,
                'belgian_diploma-other_institute_name': 'Other institute',
                'belgian_diploma-other_institute_address': 'Other institute address',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertTrue(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        belgian_diploma.refresh_from_db()

        self.assertEqual(belgian_diploma.person, self.general_admission.candidate)
        self.assertEqual(belgian_diploma.academic_graduation_year, self.academic_years[0])
        self.assertEqual(belgian_diploma.high_school_diploma, [self.files_uuids['high_school_diploma']])
        self.assertEqual(belgian_diploma.community, CommunityEnum.FRENCH_SPEAKING.name)
        self.assertEqual(belgian_diploma.educational_type, '')
        self.assertEqual(belgian_diploma.educational_other, 'Other education')
        self.assertEqual(belgian_diploma.institute, None)
        self.assertEqual(belgian_diploma.other_institute_name, 'Other institute')
        self.assertEqual(belgian_diploma.other_institute_address, 'Other institute address')

    def test_submit_valid_data_for_belgian_diploma_with_existing_foreign_diploma(self):
        self.client.force_login(self.sic_manager_user)

        foreign_diploma = ForeignHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            high_school_diploma=[self.files_uuids['high_school_diploma']],
            foreign_diploma_type=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
            equivalence=Equivalence.YES.name,
            linguistic_regime=self.french_linguistic_regime,
            other_linguistic_regime='Other linguistic regime',
            country=self.france_country,
            high_school_transcript=[self.files_uuids['high_school_transcript']],
            high_school_transcript_translation=[self.files_uuids['high_school_transcript_translation']],
            high_school_diploma_translation=[self.files_uuids['high_school_diploma_translation']],
            final_equivalence_decision_not_ue=[self.files_uuids['final_equivalence_decision_not_ue']],
            final_equivalence_decision_ue=[self.files_uuids['final_equivalence_decision_ue']],
            equivalence_decision_proof=[self.files_uuids['equivalence_decision_proof']],
        )

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'high_school_diploma_0': [self.files_uuids['high_school_diploma']],
                'diploma_type': HighSchoolDiplomaTypes.BELGIAN.name,
                'belgian_diploma-community': CommunityEnum.GERMAN_SPEAKING.name,
                'belgian_diploma-educational_type': EducationalType.PROFESSIONAL_EDUCATION.name,
                'belgian_diploma-has_other_educational_type': False,
                'belgian_diploma-educational_other': 'Other education',
                'belgian_diploma-institute': self.first_institute.pk,
                'belgian_diploma-other_institute': False,
                'belgian_diploma-other_institute_name': 'Other institute',
                'belgian_diploma-other_institute_address': 'Other institute address',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertTrue(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        belgian_diploma = BelgianHighSchoolDiploma.objects.filter(
            person=self.general_admission.candidate,
        ).first()

        self.assertIsNotNone(belgian_diploma)

        self.assertEqual(belgian_diploma.person, self.general_admission.candidate)
        self.assertEqual(belgian_diploma.academic_graduation_year, self.academic_years[0])
        self.assertEqual(belgian_diploma.high_school_diploma, [self.files_uuids['high_school_diploma']])
        self.assertEqual(belgian_diploma.community, CommunityEnum.GERMAN_SPEAKING.name)
        self.assertEqual(belgian_diploma.educational_type, '')
        self.assertEqual(belgian_diploma.educational_other, '')
        self.assertEqual(belgian_diploma.institute, self.first_institute)
        self.assertEqual(belgian_diploma.other_institute_name, '')
        self.assertEqual(belgian_diploma.other_institute_address, '')

    def test_submit_valid_data_for_belgian_diploma_with_existing_alternative(self):
        self.client.force_login(self.sic_manager_user)

        alternative = HighSchoolDiplomaAlternativeFactory(
            person=self.general_admission.candidate,
            first_cycle_admission_exam=[self.files_uuids['first_cycle_admission_exam']],
        )

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'high_school_diploma_0': [self.files_uuids['high_school_diploma']],
                'diploma_type': HighSchoolDiplomaTypes.BELGIAN.name,
                'belgian_diploma-community': CommunityEnum.GERMAN_SPEAKING.name,
                'belgian_diploma-institute': self.first_institute.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertTrue(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        belgian_diploma = BelgianHighSchoolDiploma.objects.filter(
            person=self.general_admission.candidate,
        ).first()

        self.assertIsNotNone(belgian_diploma)

        self.assertEqual(belgian_diploma.person, self.general_admission.candidate)
        self.assertEqual(belgian_diploma.academic_graduation_year, self.academic_years[0])
        self.assertEqual(belgian_diploma.high_school_diploma, [self.files_uuids['high_school_diploma']])
        self.assertEqual(belgian_diploma.community, CommunityEnum.GERMAN_SPEAKING.name)
        self.assertEqual(belgian_diploma.educational_type, '')
        self.assertEqual(belgian_diploma.educational_other, '')
        self.assertEqual(belgian_diploma.institute, self.first_institute)
        self.assertEqual(belgian_diploma.other_institute_name, '')
        self.assertEqual(belgian_diploma.other_institute_address, '')

    def test_submit_valid_data_for_foreign_diploma_with_existing_belgian_diploma(self):
        self.client.force_login(self.sic_manager_user)

        belgian_diploma = BelgianHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            academic_graduation_year=self.academic_years[1],
            high_school_diploma=[self.files_uuids['high_school_diploma']],
            community=CommunityEnum.FRENCH_SPEAKING.name,
            educational_type=EducationalType.PROFESSIONAL_EDUCATION.name,
            educational_other='Other education',
            institute=self.first_institute,
            other_institute_name='Other institute',
            other_institute_address='Other institute address',
        )

        # Choose existing values
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'high_school_diploma_0': [self.files_uuids['high_school_diploma']],
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
                'foreign_diploma-foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                'foreign_diploma-country': self.france_country.iso_code,
                'foreign_diploma-equivalence': Equivalence.YES.name,
                'foreign_diploma-linguistic_regime': self.french_linguistic_regime.code,
                'foreign_diploma-other_linguistic_regime': 'Other regime',
                'foreign_diploma-high_school_transcript_0': [self.files_uuids['high_school_transcript']],
                'foreign_diploma-high_school_transcript_translation_0': [
                    self.files_uuids['high_school_transcript_translation']
                ],
                'foreign_diploma-high_school_diploma_translation_0': [
                    self.files_uuids['high_school_diploma_translation']
                ],
                'foreign_diploma-final_equivalence_decision_not_ue_0': [
                    self.files_uuids['final_equivalence_decision_not_ue']
                ],
                'foreign_diploma-final_equivalence_decision_ue_0': [self.files_uuids['final_equivalence_decision_ue']],
                'foreign_diploma-equivalence_decision_proof_0': [self.files_uuids['equivalence_decision_proof']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertTrue(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        foreign_diploma: ForeignHighSchoolDiploma = ForeignHighSchoolDiploma.objects.filter(
            person=self.general_admission.candidate,
        ).first()

        self.assertIsNotNone(foreign_diploma)

        self.assertEqual(foreign_diploma.person, self.general_admission.candidate)
        self.assertEqual(foreign_diploma.academic_graduation_year, self.academic_years[0])
        self.assertEqual(foreign_diploma.high_school_diploma, [self.files_uuids['high_school_diploma']])
        self.assertEqual(foreign_diploma.foreign_diploma_type, ForeignDiplomaTypes.NATIONAL_BACHELOR.name)
        self.assertEqual(foreign_diploma.linguistic_regime, self.french_linguistic_regime)
        self.assertEqual(foreign_diploma.other_linguistic_regime, '')
        self.assertEqual(foreign_diploma.country, self.france_country)
        self.assertEqual(foreign_diploma.high_school_transcript, [self.files_uuids['high_school_transcript']])
        self.assertEqual(foreign_diploma.high_school_transcript_translation, [])
        self.assertEqual(foreign_diploma.high_school_diploma_translation, [])
        self.assertEqual(foreign_diploma.equivalence, Equivalence.YES.name)
        self.assertEqual(foreign_diploma.final_equivalence_decision_not_ue, [])
        self.assertEqual(
            foreign_diploma.final_equivalence_decision_ue,
            [self.files_uuids['final_equivalence_decision_ue']],
        )
        self.assertEqual(foreign_diploma.equivalence_decision_proof, [])

    def test_submit_valid_data_for_foreign_diploma_with_existing_foreign_diploma(self):
        self.client.force_login(self.sic_manager_user)

        foreign_diploma = ForeignHighSchoolDiplomaFactory(
            person=self.general_admission.candidate,
            high_school_diploma=[self.files_uuids['high_school_diploma']],
            foreign_diploma_type=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
            equivalence=Equivalence.YES.name,
            linguistic_regime=self.french_linguistic_regime,
            other_linguistic_regime='Other linguistic regime',
            country=self.france_country,
            high_school_transcript=[self.files_uuids['high_school_transcript']],
            high_school_transcript_translation=[self.files_uuids['high_school_transcript_translation']],
            high_school_diploma_translation=[self.files_uuids['high_school_diploma_translation']],
            final_equivalence_decision_not_ue=[self.files_uuids['final_equivalence_decision_not_ue']],
            final_equivalence_decision_ue=[self.files_uuids['final_equivalence_decision_ue']],
            equivalence_decision_proof=[self.files_uuids['equivalence_decision_proof']],
        )

        # Choose existing values
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'high_school_diploma_0': [self.files_uuids['high_school_diploma']],
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
                'foreign_diploma-foreign_diploma_type': ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                'foreign_diploma-country': self.france_country.iso_code,
                'foreign_diploma-equivalence': Equivalence.YES.name,
                'foreign_diploma-linguistic_regime': self.greek_linguistic_regime.code,
                'foreign_diploma-other_linguistic_regime': 'Other regime',
                'foreign_diploma-high_school_transcript_0': [self.files_uuids['high_school_transcript']],
                'foreign_diploma-high_school_transcript_translation_0': [
                    self.files_uuids['high_school_transcript_translation']
                ],
                'foreign_diploma-high_school_diploma_translation_0': [
                    self.files_uuids['high_school_diploma_translation']
                ],
                'foreign_diploma-final_equivalence_decision_not_ue_0': [
                    self.files_uuids['final_equivalence_decision_not_ue']
                ],
                'foreign_diploma-final_equivalence_decision_ue_0': [self.files_uuids['final_equivalence_decision_ue']],
                'foreign_diploma-equivalence_decision_proof_0': [self.files_uuids['equivalence_decision_proof']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertTrue(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        foreign_diploma.refresh_from_db()

        self.assertEqual(foreign_diploma.person, self.general_admission.candidate)
        self.assertEqual(foreign_diploma.academic_graduation_year, self.academic_years[0])
        self.assertEqual(foreign_diploma.high_school_diploma, [self.files_uuids['high_school_diploma']])
        self.assertEqual(foreign_diploma.foreign_diploma_type, ForeignDiplomaTypes.EUROPEAN_BACHELOR.name)
        self.assertEqual(foreign_diploma.linguistic_regime, self.greek_linguistic_regime)
        self.assertEqual(foreign_diploma.other_linguistic_regime, '')
        self.assertEqual(foreign_diploma.country, self.france_country)
        self.assertEqual(foreign_diploma.high_school_transcript, [self.files_uuids['high_school_transcript']])
        self.assertEqual(
            foreign_diploma.high_school_transcript_translation,
            [self.files_uuids['high_school_transcript_translation']],
        )
        self.assertEqual(
            foreign_diploma.high_school_diploma_translation,
            [self.files_uuids['high_school_diploma_translation']],
        )
        self.assertEqual(foreign_diploma.equivalence, '')
        self.assertEqual(foreign_diploma.final_equivalence_decision_not_ue, [])
        self.assertEqual(foreign_diploma.final_equivalence_decision_ue, [])
        self.assertEqual(foreign_diploma.equivalence_decision_proof, [])

    def test_submit_valid_data_for_foreign_diploma_with_existing_diploma_alternative(self):
        self.client.force_login(self.sic_manager_user)

        diploma_alternative = HighSchoolDiplomaAlternativeFactory(
            person=self.general_admission.candidate,
            first_cycle_admission_exam=[self.files_uuids['first_cycle_admission_exam']],
        )

        # Specify other values
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': self.academic_years[0].year,
                'high_school_diploma_0': [self.files_uuids['high_school_diploma']],
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
                'foreign_diploma-foreign_diploma_type': ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                'foreign_diploma-country': self.france_country.iso_code,
                'foreign_diploma-equivalence': Equivalence.YES.name,
                'foreign_diploma-other_linguistic_regime': 'Other regime',
                'foreign_diploma-high_school_transcript_0': [self.files_uuids['high_school_transcript']],
                'foreign_diploma-high_school_transcript_translation_0': [
                    self.files_uuids['high_school_transcript_translation']
                ],
                'foreign_diploma-high_school_diploma_translation_0': [
                    self.files_uuids['high_school_diploma_translation']
                ],
                'foreign_diploma-final_equivalence_decision_not_ue_0': [
                    self.files_uuids['final_equivalence_decision_not_ue']
                ],
                'foreign_diploma-final_equivalence_decision_ue_0': [self.files_uuids['final_equivalence_decision_ue']],
                'foreign_diploma-equivalence_decision_proof_0': [self.files_uuids['equivalence_decision_proof']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertTrue(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        # Check saved data
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.candidate.graduated_from_high_school, GotDiploma.YES.name)
        self.assertEqual(self.general_admission.candidate.graduated_from_high_school_year, self.academic_years[0])

        foreign_diploma: ForeignHighSchoolDiploma = ForeignHighSchoolDiploma.objects.filter(
            person=self.general_admission.candidate
        ).first()

        self.assertIsNotNone(foreign_diploma)

        self.assertEqual(foreign_diploma.person, self.general_admission.candidate)
        self.assertEqual(foreign_diploma.academic_graduation_year, self.academic_years[0])
        self.assertEqual(foreign_diploma.high_school_diploma, [self.files_uuids['high_school_diploma']])
        self.assertEqual(foreign_diploma.foreign_diploma_type, ForeignDiplomaTypes.EUROPEAN_BACHELOR.name)
        self.assertEqual(foreign_diploma.linguistic_regime, None)
        self.assertEqual(foreign_diploma.other_linguistic_regime, 'Other regime')
        self.assertEqual(foreign_diploma.country, self.france_country)
        self.assertEqual(foreign_diploma.high_school_transcript, [self.files_uuids['high_school_transcript']])
        self.assertEqual(
            foreign_diploma.high_school_transcript_translation,
            [self.files_uuids['high_school_transcript_translation']],
        )
        self.assertEqual(
            foreign_diploma.high_school_diploma_translation,
            [self.files_uuids['high_school_diploma_translation']],
        )
        self.assertEqual(foreign_diploma.equivalence, '')
        self.assertEqual(foreign_diploma.final_equivalence_decision_not_ue, [])
        self.assertEqual(foreign_diploma.final_equivalence_decision_ue, [])
        self.assertEqual(foreign_diploma.equivalence_decision_proof, [])

    def test_submit_foreign_diploma_with_ue_equivalence(self):
        self.client.force_login(self.sic_manager_user)

        # UE country
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.THIS_YEAR.name,
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
                'foreign_diploma-foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                'foreign_diploma-equivalence': Equivalence.YES.name,
                'foreign_diploma-country': self.france_country.iso_code,
                'foreign_diploma-linguistic_regime': self.french_linguistic_regime.code,
                'foreign_diploma-final_equivalence_decision_ue_0': [self.files_uuids['final_equivalence_decision_ue']],
                'foreign_diploma-equivalence_decision_proof_0': [self.files_uuids['equivalence_decision_proof']],
                'foreign_diploma-final_equivalence_decision_not_ue_0': [
                    self.files_uuids['final_equivalence_decision_not_ue']
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).first()

        self.assertIsNotNone(foreign_diploma)

        self.assertEqual(foreign_diploma.equivalence, Equivalence.YES.name)
        self.assertEqual(
            foreign_diploma.final_equivalence_decision_ue,
            [self.files_uuids['final_equivalence_decision_ue']],
        )
        self.assertEqual(foreign_diploma.equivalence_decision_proof, [])
        self.assertEqual(foreign_diploma.final_equivalence_decision_not_ue, [])

    def test_submit_foreign_diploma_with_pending_ue_equivalence(self):
        self.client.force_login(self.sic_manager_user)

        # Medical and dentistry trainings -> UE equivalence
        self.general_admission.training.main_domain = DomainFactory(code='11AB')
        self.general_admission.training.save()

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.THIS_YEAR.name,
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
                'foreign_diploma-foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                'foreign_diploma-equivalence': Equivalence.PENDING.name,
                'foreign_diploma-country': self.us_country.iso_code,
                'foreign_diploma-linguistic_regime': self.french_linguistic_regime.code,
                'foreign_diploma-final_equivalence_decision_ue_0': [self.files_uuids['final_equivalence_decision_ue']],
                'foreign_diploma-equivalence_decision_proof_0': [self.files_uuids['equivalence_decision_proof']],
                'foreign_diploma-final_equivalence_decision_not_ue_0': [
                    self.files_uuids['final_equivalence_decision_not_ue']
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).first()

        self.assertIsNotNone(foreign_diploma)

        self.assertEqual(foreign_diploma.equivalence, Equivalence.PENDING.name)
        self.assertEqual(foreign_diploma.final_equivalence_decision_ue, [])
        self.assertEqual(foreign_diploma.equivalence_decision_proof, [self.files_uuids['equivalence_decision_proof']])
        self.assertEqual(foreign_diploma.final_equivalence_decision_not_ue, [])

    def test_submit_foreign_diploma_with_no_ue_equivalence(self):
        self.client.force_login(self.sic_manager_user)

        # UE country
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.THIS_YEAR.name,
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
                'foreign_diploma-foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                'foreign_diploma-equivalence': Equivalence.NO.name,
                'foreign_diploma-country': self.france_country.iso_code,
                'foreign_diploma-linguistic_regime': self.french_linguistic_regime.code,
                'foreign_diploma-final_equivalence_decision_ue_0': [self.files_uuids['final_equivalence_decision_ue']],
                'foreign_diploma-equivalence_decision_proof_0': [self.files_uuids['equivalence_decision_proof']],
                'foreign_diploma-final_equivalence_decision_not_ue_0': [
                    self.files_uuids['final_equivalence_decision_not_ue']
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).first()

        self.assertIsNotNone(foreign_diploma)

        self.assertEqual(foreign_diploma.equivalence, Equivalence.NO.name)
        self.assertEqual(foreign_diploma.final_equivalence_decision_ue, [])
        self.assertEqual(foreign_diploma.equivalence_decision_proof, [])
        self.assertEqual(foreign_diploma.final_equivalence_decision_not_ue, [])

    def test_submit_foreign_diploma_with_not_ue_equivalence(self):
        self.client.force_login(self.sic_manager_user)

        # Not UE country
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.THIS_YEAR.name,
                'diploma_type': HighSchoolDiplomaTypes.FOREIGN.name,
                'foreign_diploma-foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                'foreign_diploma-country': self.us_country.iso_code,
                'foreign_diploma-equivalence': Equivalence.NO.name,
                'foreign_diploma-linguistic_regime': self.french_linguistic_regime.code,
                'foreign_diploma-final_equivalence_decision_ue_0': [self.files_uuids['final_equivalence_decision_ue']],
                'foreign_diploma-equivalence_decision_proof_0': [self.files_uuids['equivalence_decision_proof']],
                'foreign_diploma-final_equivalence_decision_not_ue_0': [
                    self.files_uuids['final_equivalence_decision_not_ue']
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        foreign_diploma = ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).first()

        self.assertIsNotNone(foreign_diploma)

        self.assertEqual(foreign_diploma.equivalence, '')
        self.assertEqual(foreign_diploma.final_equivalence_decision_ue, [])
        self.assertEqual(foreign_diploma.equivalence_decision_proof, [])
        self.assertEqual(
            foreign_diploma.final_equivalence_decision_not_ue, [self.files_uuids['final_equivalence_decision_not_ue']]
        )

    def test_submit_diploma_alternative_without_existing_diploma(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'first_cycle_admission_exam_0': [self.files_uuids['first_cycle_admission_exam']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        diploma_alternative = HighSchoolDiplomaAlternative.objects.filter(
            person=self.general_admission.candidate,
        ).first()

        self.assertIsNotNone(diploma_alternative)

        self.assertEqual(
            diploma_alternative.first_cycle_admission_exam, [self.files_uuids['first_cycle_admission_exam']]
        )

    def test_submit_diploma_alternative_with_existing_belgian_diploma(self):
        self.client.force_login(self.sic_manager_user)

        BelgianHighSchoolDiplomaFactory(person=self.general_admission.candidate)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'first_cycle_admission_exam_0': [self.files_uuids['first_cycle_admission_exam']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertTrue(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        diploma_alternative = HighSchoolDiplomaAlternative.objects.filter(
            person=self.general_admission.candidate,
        ).first()

        self.assertIsNotNone(diploma_alternative)

        self.assertEqual(
            diploma_alternative.first_cycle_admission_exam, [self.files_uuids['first_cycle_admission_exam']]
        )

    def test_submit_diploma_alternative_with_existing_foreign_diploma(self):
        self.client.force_login(self.sic_manager_user)

        ForeignHighSchoolDiplomaFactory(person=self.general_admission.candidate)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'first_cycle_admission_exam_0': [self.files_uuids['first_cycle_admission_exam']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertTrue(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        diploma_alternative = HighSchoolDiplomaAlternative.objects.filter(
            person=self.general_admission.candidate,
        ).first()

        self.assertIsNotNone(diploma_alternative)

        self.assertEqual(
            diploma_alternative.first_cycle_admission_exam,
            [self.files_uuids['first_cycle_admission_exam']],
        )

    def test_submit_diploma_alternative_with_existing_diploma_alternative(self):
        self.client.force_login(self.sic_manager_user)

        HighSchoolDiplomaAlternative(person=self.general_admission.candidate)

        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'first_cycle_admission_exam_0': [self.files_uuids['first_cycle_admission_exam']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertFalse(BelgianHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertFalse(ForeignHighSchoolDiploma.objects.filter(person=self.general_admission.candidate).exists())
        self.assertTrue(HighSchoolDiplomaAlternative.objects.filter(person=self.general_admission.candidate).exists())

        diploma_alternative = HighSchoolDiplomaAlternative.objects.filter(
            person=self.general_admission.candidate,
        ).first()

        self.assertIsNotNone(diploma_alternative)

        self.assertEqual(
            diploma_alternative.first_cycle_admission_exam,
            [self.files_uuids['first_cycle_admission_exam']],
        )

    def test_submit_answers_to_specific_questions(self):
        self.client.force_login(self.sic_manager_user)

        text_question = TextAdmissionFormItemFactory()
        text_question_uuid = str(text_question.uuid)

        text_question_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=text_question,
            academic_year=self.training.academic_year,
            tab=Onglets.CHOIX_FORMATION.name,
            required=True,
        )

        self.general_admission.specific_question_answers[text_question_uuid] = 'My first answer'
        self.general_admission.save(update_fields=['specific_question_answers'])

        # No specific question in the form
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.specific_question_answers.get(text_question_uuid), 'My first answer')
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)

        # One specific question in the form
        text_question_instantiation.tab = Onglets.ETUDES_SECONDAIRES.name
        text_question_instantiation.save(update_fields=['tab'])

        # But no answer
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn('specific_question_answers', form.errors)

        self.assertEqual(
            len(getattr(form.fields['specific_question_answers'].fields[0], 'errors', [])),
            1,
        )

        # And one answer
        response = self.client.post(
            self.form_url,
            data={
                'graduated_from_high_school': GotDiploma.NO.name,
                'specific_question_answers_0': 'My second answer',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.specific_question_answers.get(text_question_uuid), 'My second answer')
