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
import datetime
import uuid
from unittest import mock

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.constants import PDF_MIME_TYPE, FIELD_REQUIRED_MESSAGE
from admission.contrib.models.base import (
    AdmissionProfessionalValuatedExperiences,
)
from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_profile.models import ProfessionalExperience
from osis_profile.models.enums.curriculum import ActivityType, ActivitySector
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2023-01-01')
class CurriculumNonEducationalExperienceFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020]]
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=cls.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user

        cls.file_uuid = uuid.uuid4()

    def setUp(self):
        # Create data
        self.experience: ProfessionalExperience = ProfessionalExperienceFactory(
            person=self.general_admission.candidate,
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 12, 31),
            type=ActivityType.WORK.name,
            role='Function',
            sector=ActivitySector.PRIVATE.name,
            institute_name='Institute',
            certificate=[self.file_uuid],
            activity='Activity',
        )

        # Mock osis document api
        patcher = mock.patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value: value

        # Targeted url
        self.form_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.create_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational_create',
            uuid=self.general_admission.uuid,
        )

    def test_update_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        month_choices = [
            ['', ' - '],
            [1, 'Janvier'],
            [2, 'Février'],
            [3, 'Mars'],
            [4, 'Avril'],
            [5, 'Mai'],
            [6, 'Juin'],
            [7, 'Juillet'],
            [8, 'Août'],
            [9, 'Septembre'],
            [10, 'Octobre'],
            [11, 'Novembre'],
            [12, 'Décembre'],
        ]

        year_choices = [['', ' - ']] + [[year, year] for year in range(2023, 1900, -1)]

        # Start date
        self.assertEqual(form['start_date_month'].value(), 1)
        self.assertEqual(
            [[choice[0], choice[1]] for choice in form.fields['start_date_month'].choices],
            month_choices,
        )
        self.assertEqual(form['start_date_year'].value(), 2020)
        self.assertEqual(
            [[choice[0], choice[1]] for choice in form.fields['start_date_year'].choices],
            year_choices,
        )

        # End date
        self.assertEqual(form['end_date_month'].value(), 12)
        self.assertEqual(
            [[choice[0], choice[1]] for choice in form.fields['end_date_month'].choices],
            month_choices,
        )
        self.assertEqual(form['end_date_year'].value(), 2021)
        self.assertEqual(
            [[choice[0], choice[1]] for choice in form.fields['end_date_year'].choices],
            year_choices,
        )

        # Type
        self.assertEqual(form['type'].value(), ActivityType.WORK.name)

        # Function
        self.assertEqual(form['role'].value(), 'Function')

        # Sector
        self.assertEqual(form['sector'].value(), ActivitySector.PRIVATE.name)

        # Institute
        self.assertEqual(form['institute_name'].value(), 'Institute')

        # Certificate
        self.assertEqual(form['certificate'].value(), [self.file_uuid])

        # Activity
        self.assertEqual(form['activity'].value(), 'Activity')

    def test_submit_form_with_missing_fields(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('start_date_month', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('start_date_year', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('end_date_month', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('end_date_year', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('type', []))

    def test_submit_form_with_missing_fields_for_work(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            {
                'start_date_month': 1,
                'start_date_year': 2020,
                'end_date_month': 12,
                'end_date_year': 2021,
                'type': ActivityType.WORK.name,
                'activity': 'Activity',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('role', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('sector', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('institute_name', []))

        self.assertEqual(form.cleaned_data['activity'], '')

    def test_submit_form_with_missing_fields_for_other_activity(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            {
                'start_date_month': 1,
                'start_date_year': 2020,
                'end_date_month': 12,
                'end_date_year': 2021,
                'type': ActivityType.OTHER.name,
                'role': 'Role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('activity', []))

        self.assertEqual(form.cleaned_data['role'], '')
        self.assertEqual(form.cleaned_data['sector'], '')
        self.assertEqual(form.cleaned_data['institute_name'], '')

    def test_submit_valid_form_for_work(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            {
                'start_date_month': 2,
                'start_date_year': 2019,
                'end_date_month': 3,
                'end_date_year': 2022,
                'type': ActivityType.WORK.name,
                'role': 'Role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
                'activity': 'Activity',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.experience.refresh_from_db()

        self.assertEqual(self.experience.start_date, datetime.date(2019, 2, 1))
        self.assertEqual(self.experience.end_date, datetime.date(2022, 3, 31))
        self.assertEqual(self.experience.type, ActivityType.WORK.name)
        self.assertEqual(self.experience.role, 'Role')
        self.assertEqual(self.experience.sector, ActivitySector.PRIVATE.name)
        self.assertEqual(self.experience.institute_name, 'Institute')
        self.assertEqual(self.experience.activity, '')

    def test_submit_valid_form_for_other_activity(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            {
                'start_date_month': 2,
                'start_date_year': 2019,
                'end_date_month': 3,
                'end_date_year': 2022,
                'type': ActivityType.OTHER.name,
                'role': 'Role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
                'activity': 'Activity',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.experience.refresh_from_db()

        self.assertEqual(self.experience.start_date, datetime.date(2019, 2, 1))
        self.assertEqual(self.experience.end_date, datetime.date(2022, 3, 31))
        self.assertEqual(self.experience.type, ActivityType.OTHER.name)
        self.assertEqual(self.experience.role, '')
        self.assertEqual(self.experience.sector, '')
        self.assertEqual(self.experience.institute_name, '')
        self.assertEqual(self.experience.activity, 'Activity')

    def test_submit_valid_form_for_create_a_new_work_activity(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.create_url,
            {
                'start_date_month': 2,
                'start_date_year': 2019,
                'end_date_month': 3,
                'end_date_year': 2022,
                'type': ActivityType.WORK.name,
                'role': 'My new role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
                'activity': 'Activity',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.experience.refresh_from_db()

        created_experience = ProfessionalExperience.objects.filter(
            role='My new role',
            person=self.general_admission.candidate,
        ).first()

        self.assertIsNotNone(created_experience)

        self.assertEqual(created_experience.start_date, datetime.date(2019, 2, 1))
        self.assertEqual(created_experience.end_date, datetime.date(2022, 3, 31))
        self.assertEqual(created_experience.type, ActivityType.WORK.name)
        self.assertEqual(created_experience.role, 'My new role')
        self.assertEqual(created_experience.sector, ActivitySector.PRIVATE.name)
        self.assertEqual(created_experience.institute_name, 'Institute')
        self.assertEqual(created_experience.activity, '')

        # Check that the experience has been valuated
        self.assertTrue(
            AdmissionProfessionalValuatedExperiences.objects.filter(
                baseadmission_id=self.general_admission.uuid,
                professionalexperience_id=created_experience.uuid,
            ).exists()
        )

        # Check that the checklist has been updated
        self.general_admission.refresh_from_db()

        last_experience_checklist = self.general_admission.checklist['current']['parcours_anterieur']['enfants'][-1]

        self.assertEqual(
            last_experience_checklist['extra']['identifiant'],
            str(created_experience.uuid),
        )

        self.assertEqual(
            last_experience_checklist,
            {
                'libelle': 'To be processed',
                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                'extra': {
                    'identifiant': str(created_experience.uuid),
                    'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                    'commentaire_authentification': '',
                },
                'enfants': [],
            },
        )


class CurriculumNonEducationalExperienceDeleteViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]
        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=cls.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user
        cls.file_uuid = uuid.uuid4()

    def setUp(self):
        # Create data
        self.experience: ProfessionalExperience = ProfessionalExperienceFactory(
            person=self.general_admission.candidate,
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 12, 31),
            type=ActivityType.WORK.name,
            role='Function',
            sector=ActivitySector.PRIVATE.name,
            institute_name='Institute',
            certificate=[self.file_uuid],
            activity='Activity',
        )

        # Targeted url
        self.delete_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational_delete',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )

    def test_delete_experience_from_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_experience_from_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.delete(self.delete_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_delete_unknown_experience_returns_404(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.delete(
            resolve_url(
                'admission:general-education:update:curriculum:non_educational_delete',
                uuid=self.general_admission.uuid,
                experience_uuid=uuid.uuid4(),
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_known_experience(self):
        self.client.force_login(self.sic_manager_user)

        # Simulate a valuated experience
        AdmissionProfessionalValuatedExperiences.objects.create(
            baseadmission_id=self.general_admission.uuid,
            professionalexperience_id=self.experience.uuid,
        )

        self.general_admission.checklist['current']['parcours_anterieur']['enfants'] = [
            Checklist.initialiser_checklist_experience(experience_uuid=self.experience.uuid).to_dict()
        ]

        self.general_admission.save()

        response = self.client.delete(self.delete_url)

        self.assertFalse(ProfessionalExperience.objects.filter(uuid=self.experience.uuid).exists())

        self.assertFalse(
            AdmissionProfessionalValuatedExperiences.objects.filter(
                professionalexperience_id=self.experience.uuid
            ).exists()
        )

        self.general_admission.refresh_from_db()

        self.assertEqual(
            self.general_admission.checklist['current']['parcours_anterieur']['enfants'],
            [],
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
