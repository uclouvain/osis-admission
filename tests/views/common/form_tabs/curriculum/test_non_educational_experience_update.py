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

import datetime
import uuid
from unittest import mock

import freezegun
from django.conf import settings
from django.forms import MultipleHiddenInput
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.events import ExperienceNonAcademiqueCandidatCreeeOuModifieeEvent
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.shared_kernel.domain.model.enums.authentification import (
    EtatAuthentificationParcours,
)
from admission.ddd.admission.shared_kernel.enums.emplacement_document import (
    OngletsDemande,
)
from admission.models import ContinuingEducationAdmission, DoctorateAdmission
from admission.models import EPCInjection as AdmissionEPCInjection
from admission.models.base import AdmissionProfessionalValuatedExperiences
from admission.models.epc_injection import (
    EPCInjectionStatus as AdmissionEPCInjectionStatus,
)
from admission.models.epc_injection import EPCInjectionType
from admission.models.general_education import GeneralEducationAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.curriculum import (
    AdmissionProfessionalValuatedExperiencesFactory,
    ProfessionalExperienceFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_profile.models import ProfessionalExperience
from osis_profile.models.enums.curriculum import ActivitySector, ActivityType
from osis_profile.models.epc_injection import EPCInjection as CurriculumEPCInjection
from osis_profile.models.epc_injection import (
    EPCInjectionStatus as CurriculumEPCInjectionStatus,
)
from osis_profile.models.epc_injection import ExperienceType
from reference.tests.factories.country import CountryFactory


# TODO: Remove duplicate tests with osis_profile
@freezegun.freeze_time('2023-01-01')
class CurriculumNonEducationalExperienceFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020]]

        entity = EntityVersionFactory().entity

        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=entity,
            training__academic_year=cls.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        cls.other_continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training__management_entity=entity,
            training__academic_year=cls.academic_years[0],
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        cls.doctorate_admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=entity,
            training__academic_year=cls.academic_years[0],
            candidate=cls.general_admission.candidate,
            submitted=True,
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=entity).person.user
        cls.general_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.general_admission.training.education_group,
        ).person.user
        cls.other_continuing_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.other_continuing_admission.training.education_group,
        ).person.user
        cls.doctorate_program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.doctorate_admission.training.education_group,
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
        patcher = mock.patch(
            "osis_document_components.services.get_remote_token", side_effect=lambda value, **kwargs: value
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document_components.services.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document_components.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: value

        # Targeted urls
        self.general_form_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational',
            uuid=self.general_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.general_create_url = resolve_url(
            'admission:general-education:update:curriculum:non_educational_create',
            uuid=self.general_admission.uuid,
        )
        self.doctorate_form_url = resolve_url(
            'admission:doctorate:update:curriculum:non_educational',
            uuid=self.doctorate_admission.uuid,
            experience_uuid=self.experience.uuid,
        )
        self.doctorate_create_url = resolve_url(
            'admission:doctorate:update:curriculum:non_educational_create',
            uuid=self.doctorate_admission.uuid,
        )

        # Mock publish
        patcher = mock.patch('infrastructure.utils.MessageBus.publish')
        self.mock_publish = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('django.db.transaction.on_commit', side_effect=lambda f: f())
        self.mock_on_commit = patcher.start()
        self.addCleanup(patcher.stop)

    def test_general_update_curriculum_is_not_allowed_for_fac_users(self):
        self.client.force_login(self.general_program_manager_user)
        response = self.client.get(self.general_form_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_general_update_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.general_form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_general_update_curriculum_is_not_allowed_for_injected_experiences(self):
        self.client.force_login(self.sic_manager_user)

        # The experience come from EPC
        self.experience.external_id = 'EPC1'
        self.experience.save(update_fields=['external_id'])

        response = self.client.get(self.general_form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Reset the experience
        self.experience.external_id = ''
        self.experience.save(update_fields=['external_id'])

        # The experience has been injected from the curriculum
        cv_injection = CurriculumEPCInjection.objects.create(
            person=self.general_admission.candidate,
            type_experience=ExperienceType.PROFESSIONAL.name,
            experience_uuid=self.experience.uuid,
            status=CurriculumEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.general_form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        cv_injection.delete()

        # The experience has been injected from another admission
        other_admission = GeneralEducationAdmissionFactory(candidate=self.general_admission.candidate)

        other_admission_injection = AdmissionEPCInjection.objects.create(
            admission=other_admission,
            type=EPCInjectionType.DEMANDE.name,
            status=AdmissionEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.general_form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        other_valuation = AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=other_admission,
            professionalexperience=self.experience,
        )

        response = self.client.get(self.general_form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        other_admission.delete()
        other_valuation.delete()

        # The current admission has been injected
        admission_injection = AdmissionEPCInjection.objects.create(
            admission=self.general_admission,
            type=EPCInjectionType.DEMANDE.name,
            status=AdmissionEPCInjectionStatus.OK.name,
        )

        response = self.client.get(self.general_form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_general_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.general_form_url)

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

    def test_general_submit_form_with_missing_fields(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(self.general_form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('start_date_month', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('start_date_year', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('end_date_month', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('end_date_year', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('type', []))

    def test_general_submit_form_with_missing_fields_for_work(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.general_form_url,
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

    def test_general_submit_form_with_missing_fields_for_other_activity(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.general_form_url,
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

    def test_general_submit_valid_form_for_work(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.general_form_url,
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
                'certificate_0': [self.file_uuid],
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

        # Check the admission
        self.general_admission.refresh_from_db()
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertNotIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.general_admission.requested_documents,
        )

        # Check that an event has been sent
        self.mock_publish.assert_called_once_with(
            ExperienceNonAcademiqueCandidatCreeeOuModifieeEvent(
                matricule=self.general_admission.candidate.global_id,
                transaction_id=mock.ANY,
                entity_id=mock.ANY,
            )
        )

    def test_general_submit_valid_form_for_other_activity_and_redirect(self):
        self.client.force_login(self.sic_manager_user)

        admission_url = resolve_url('admission')
        expected_url = f'{admission_url}#custom_hash'

        response = self.client.post(
            f'{self.general_form_url}?next={admission_url}&next_hash_url=custom_hash',
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
                'certificate_0': [self.file_uuid],
            },
        )

        self.assertRedirects(response=response, fetch_redirect_response=False, expected_url=expected_url)

        self.experience.refresh_from_db()

        self.assertEqual(self.experience.start_date, datetime.date(2019, 2, 1))
        self.assertEqual(self.experience.end_date, datetime.date(2022, 3, 31))
        self.assertEqual(self.experience.type, ActivityType.OTHER.name)
        self.assertEqual(self.experience.role, '')
        self.assertEqual(self.experience.sector, '')
        self.assertEqual(self.experience.institute_name, '')
        self.assertEqual(self.experience.activity, 'Activity')

    def test_general_submit_valid_form_for_create_a_new_work_activity(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.general_create_url,
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
                'certificate_0': [self.file_uuid],
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
                },
                'enfants': [],
            },
        )

    def test_continuing_update_curriculum_for_fac_users(self):
        self.client.force_login(self.other_continuing_program_manager_user)

        experience = ProfessionalExperienceFactory(
            person=self.other_continuing_admission.candidate,
        )

        url = resolve_url(
            'admission:continuing-education:update:curriculum:non_educational',
            uuid=self.other_continuing_admission.uuid,
            experience_uuid=experience.uuid,
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        doctorate_admission = DoctorateAdmissionFactory(
            candidate=experience.person,
            submitted=True,
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        doctorate_admission.delete()

        general_admission = GeneralEducationAdmissionFactory(
            candidate=experience.person,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_continuing_update_curriculum_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)

        experience = ProfessionalExperienceFactory(
            person=self.other_continuing_admission.candidate,
        )

        url = resolve_url(
            'admission:continuing-education:update:curriculum:non_educational',
            uuid=self.other_continuing_admission.uuid,
            experience_uuid=experience.uuid,
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']
        self.assertEqual(form.fields['certificate'].disabled, True)
        self.assertIsInstance(form.fields['certificate'].widget, MultipleHiddenInput)

        doctorate_admission = DoctorateAdmissionFactory(
            candidate=experience.person,
            submitted=True,
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        doctorate_admission.delete()

        general_admission = GeneralEducationAdmissionFactory(
            candidate=experience.person,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_continuing_submit_form(self):
        self.client.force_login(self.sic_manager_user)

        experience = ProfessionalExperienceFactory(
            person=self.other_continuing_admission.candidate,
        )
        experience_certificate = experience.certificate

        url = resolve_url(
            'admission:continuing-education:update:curriculum:non_educational',
            uuid=self.other_continuing_admission.uuid,
            experience_uuid=experience.uuid,
        )

        response = self.client.post(
            url,
            {
                'start_date_month': 1,
                'start_date_year': 2020,
                'end_date_month': 5,
                'end_date_year': 2020,
                'type': ActivityType.INTERNSHIP.name,
                'role': 'Role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
                'activity': 'Activity',
                'certificate_0': [self.file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check the experience
        experience.refresh_from_db()

        self.assertEqual(experience.start_date, datetime.date(2020, 1, 1))
        self.assertEqual(experience.end_date, datetime.date(2020, 5, 31))
        self.assertEqual(experience.type, ActivityType.INTERNSHIP.name)
        self.assertEqual(experience.role, '')
        self.assertEqual(experience.sector, '')
        self.assertEqual(experience.institute_name, '')
        self.assertEqual(experience.activity, '')
        self.assertEqual(experience.certificate, experience_certificate)

        # Check the admission
        self.other_continuing_admission.refresh_from_db()
        self.assertEqual(self.other_continuing_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.other_continuing_admission.last_update_author, self.sic_manager_user.person)

    def test_doctorate_update_curriculum_is_allowed_for_fac_users(self):
        other_admission = DoctorateAdmissionFactory(
            training=self.doctorate_admission.training,
            candidate=self.doctorate_admission.candidate,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        self.client.force_login(self.doctorate_program_manager_user)
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:non_educational',
                uuid=other_admission.uuid,
                experience_uuid=self.experience.uuid,
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_doctorate_update_curriculum_is_allowed_for_sic_users(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.doctorate_form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']
        self.assertEqual(form.fields['certificate'].disabled, False)

    def test_doctorate_submit_form(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.doctorate_form_url,
            {
                'start_date_month': 1,
                'start_date_year': 2020,
                'end_date_month': 5,
                'end_date_year': 2020,
                'type': ActivityType.INTERNSHIP.name,
                'role': 'Role',
                'sector': ActivitySector.PRIVATE.name,
                'institute_name': 'Institute',
                'activity': 'Activity',
                'certificate_0': [self.file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check the experience
        self.experience.refresh_from_db()

        self.assertEqual(self.experience.start_date, datetime.date(2020, 1, 1))
        self.assertEqual(self.experience.end_date, datetime.date(2020, 5, 31))
        self.assertEqual(self.experience.type, ActivityType.INTERNSHIP.name)
        self.assertEqual(self.experience.role, '')
        self.assertEqual(self.experience.sector, '')
        self.assertEqual(self.experience.institute_name, '')
        self.assertEqual(self.experience.activity, '')
        self.assertEqual(self.experience.certificate, [self.file_uuid])

        # Check the admission
        self.doctorate_admission.refresh_from_db()
        self.assertEqual(self.doctorate_admission.modified_at, datetime.datetime.now())
        self.assertEqual(self.doctorate_admission.last_update_author, self.sic_manager_user.person)
