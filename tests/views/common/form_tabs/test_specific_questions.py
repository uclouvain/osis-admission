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
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext
from rest_framework import status

from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.constants import PDF_MIME_TYPE
from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories.diplomatic_post import DiplomaticPostFactory
from admission.tests.factories.form_item import (
    AdmissionFormItemInstantiationFactory,
    MessageAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
    CandidateFactory,
    ProgramManagerRoleFactory,
)
from base.forms.utils import EMPTY_CHOICE, FIELD_REQUIRED_MESSAGE
from base.models.enums.person_address_type import PersonAddressType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import Master120TrainingFactory, EducationGroupYearBachelorFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_address import PersonAddressFactory
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2022-01-01')
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class SpecificQuestionsFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        cls.ca_country = CountryFactory(iso_code='CA', european_union=False)

        first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(
            entity=first_doctoral_commission,
        )

        cls.master_training = Master120TrainingFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
        )
        cls.bachelor_training = EducationGroupYearBachelorFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
        )
        cls.bachelor_training_with_quota = EducationGroupYearBachelorFactory(
            management_entity=first_doctoral_commission,
            academic_year=cls.academic_years[1],
            acronym=SIGLES_WITH_QUOTA[0],
            partial_acronym=SIGLES_WITH_QUOTA[0],
        )

        cls.specific_questions = [
            AdmissionFormItemInstantiationFactory(
                form_item=TextAdmissionFormItemFactory(),
                tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
                academic_year=cls.academic_years[1],
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=MessageAdmissionFormItemFactory(),
                tab=Onglets.CURRICULUM.name,
                academic_year=cls.academic_years[1],
            ),
        ]

        cls.diplomatic_post = DiplomaticPostFactory(
            name_fr='Londres',
            name_en='London',
            email='london@example.be',
        )

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.master_training.education_group
        ).person.user

        cls.file_uuids = {
            'formulaire_modification_inscription': uuid.uuid4(),
            'attestation_inscription_reguliere': uuid.uuid4(),
            'documents_additionnels': uuid.uuid4(),
        }

    def setUp(self):
        # Mock osis document api
        patcher = mock.patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: value

    def test_general_specific_questions_access(self):
        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.master_training,
            candidate__language=settings.LANGUAGE_CODE_EN,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            determined_academic_year=self.academic_years[1],
            is_non_resident=False,
            diplomatic_post=self.diplomatic_post,
        )

        url = resolve_url('admission:general-education:update:specific-questions', uuid=general_admission.uuid)

        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.program_manager_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_general_specific_questions_form_initialization_for_a_master(self):
        self.client.force_login(self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.master_training,
            candidate__language=settings.LANGUAGE_CODE_EN,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            determined_academic_year=self.academic_years[1],
            is_non_resident=False,
        )

        url = resolve_url('admission:general-education:update:specific-questions', uuid=general_admission.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, general_admission.uuid)

        form = response.context['form']

        # One specific question has been found
        self.assertEqual(len(form.fields['reponses_questions_specifiques'].fields), 1)

        # The visa question is not used
        self.assertEqual(form.fields['poste_diplomatique'].disabled, True)

        # The pools questions are not used
        self.assertNotIn('est_non_resident_au_sens_decret', form.fields)
        self.assertNotIn('est_bachelier_belge', form.fields)
        self.assertNotIn('est_modification_inscription_externe', form.fields)
        self.assertNotIn('formulaire_modification_inscription', form.fields)
        self.assertNotIn('est_reorientation_inscription_externe', form.fields)
        self.assertNotIn('attestation_inscription_reguliere', form.fields)

    def test_general_specific_questions_form_initialization_for_a_bachelor(self):
        self.client.force_login(self.sic_manager_user)

        # Bachelor
        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.bachelor_training_with_quota,
            candidate__language=settings.LANGUAGE_CODE_EN,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            determined_academic_year=self.academic_years[1],
            is_non_resident=False,
            diplomatic_post=self.diplomatic_post,
            candidate__country_of_citizenship=self.ca_country,
        )
        PersonAddressFactory(
            person=general_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
            country=self.ca_country,
        )

        url = resolve_url('admission:general-education:update:specific-questions', uuid=general_admission.uuid)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        form = response.context['form']

        # Display visa question: not ue+5 nationality and foreign residential country
        self.assertEqual(form.fields['poste_diplomatique'].disabled, False)
        self.assertEqual(form.fields['poste_diplomatique'].required, True)
        self.assertEqual(
            form.fields['poste_diplomatique'].choices,
            EMPTY_CHOICE + ((self.diplomatic_post.code, self.diplomatic_post.name_fr),),
        )
        self.assertEqual(len(form.fields['poste_diplomatique'].widget.forward), 1)
        self.assertEqual(form.fields['poste_diplomatique'].widget.forward[0].val, self.ca_country.iso_code)
        self.assertEqual(form.fields['poste_diplomatique'].widget.forward[0].dst, 'country')

        # Display pool questions: bachelor with quota
        self.assertIn('est_non_resident_au_sens_decret', form.fields)
        self.assertIn('est_bachelier_belge', form.fields)
        self.assertIn('est_modification_inscription_externe', form.fields)
        self.assertIn('formulaire_modification_inscription', form.fields)
        self.assertIn('est_reorientation_inscription_externe', form.fields)
        self.assertIn('attestation_inscription_reguliere', form.fields)

        # Hide the resident question because the training has no quota
        general_admission.training = self.bachelor_training
        general_admission.save()

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        form = response.context['form']
        self.assertNotIn('est_non_resident_au_sens_decret', form.fields)
        self.assertIn('est_bachelier_belge', form.fields)
        self.assertIn('est_modification_inscription_externe', form.fields)
        self.assertIn('formulaire_modification_inscription', form.fields)
        self.assertIn('est_reorientation_inscription_externe', form.fields)
        self.assertIn('attestation_inscription_reguliere', form.fields)

    def test_general_specific_questions_form_submit_with_a_master(self):
        self.client.force_login(self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.master_training,
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            determined_academic_year=self.academic_years[1],
            is_non_resident=False,
        )

        url = resolve_url('admission:general-education:update:specific-questions', uuid=general_admission.uuid)
        detail_url = resolve_url('admission:general-education:specific-questions', uuid=general_admission.uuid)

        # No data
        response = self.client.post(url, data={})

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(
            general_admission.specific_question_answers.get(str(self.specific_questions[0].form_item.uuid)),
            '',
        )
        self.assertEqual(general_admission.diplomatic_post, None)
        self.assertEqual(general_admission.is_non_resident, None)
        self.assertEqual(general_admission.is_belgian_bachelor, None)
        self.assertEqual(general_admission.additional_documents, [])
        self.assertEqual(general_admission.is_external_reorientation, None)
        self.assertEqual(general_admission.regular_registration_proof, [])
        self.assertEqual(general_admission.is_external_modification, None)
        self.assertEqual(general_admission.registration_change_form, [])
        self.assertEqual(general_admission.modified_at, datetime.datetime.today())
        self.assertEqual(general_admission.last_update_author, self.sic_manager_user.person)
        self.assertIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            general_admission.requested_documents,
        )

        # With data
        response = self.client.post(
            url,
            data={
                'reponses_questions_specifiques_0': 'My answer',
                'poste_diplomatique': self.diplomatic_post.code,
                'est_non_resident_au_sens_decret': True,
                'est_bachelier_belge': True,
                'est_modification_inscription_externe': True,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': True,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
                'documents_additionnels_0': [self.file_uuids['documents_additionnels']],
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(
            general_admission.specific_question_answers.get(str(self.specific_questions[0].form_item.uuid)),
            'My answer',
        )
        self.assertEqual(general_admission.diplomatic_post, None)
        self.assertEqual(general_admission.is_non_resident, None)
        self.assertEqual(general_admission.is_belgian_bachelor, None)
        self.assertEqual(general_admission.additional_documents, [self.file_uuids['documents_additionnels']])
        self.assertEqual(general_admission.is_external_reorientation, None)
        self.assertEqual(general_admission.regular_registration_proof, [])
        self.assertEqual(general_admission.is_external_modification, None)
        self.assertEqual(general_admission.registration_change_form, [])

        # With diplomatic post
        general_admission.candidate.country_of_citizenship = self.ca_country
        general_admission.candidate.save()

        PersonAddressFactory(
            person=general_admission.candidate,
            label=PersonAddressType.RESIDENTIAL.name,
            country=self.ca_country,
        )

        response = self.client.post(
            url,
            data={
                'poste_diplomatique': self.diplomatic_post.code,
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(general_admission.diplomatic_post, self.diplomatic_post)

    def test_general_specific_questions_form_submit_with_a_bachelor_with_quota(self):
        self.client.force_login(self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.bachelor_training_with_quota,
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            determined_academic_year=self.academic_years[1],
            is_non_resident=False,
        )

        url = resolve_url('admission:general-education:update:specific-questions', uuid=general_admission.uuid)
        detail_url = resolve_url('admission:general-education:specific-questions', uuid=general_admission.uuid)

        # With data -> reinscription
        response = self.client.post(
            url,
            data={
                'poste_diplomatique': self.diplomatic_post.code,
                'est_non_resident_au_sens_decret': False,
                'est_bachelier_belge': True,
                'est_modification_inscription_externe': False,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': True,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(general_admission.diplomatic_post, None)
        self.assertEqual(general_admission.is_non_resident, False)
        self.assertEqual(general_admission.is_belgian_bachelor, True)
        self.assertEqual(general_admission.is_external_reorientation, True)
        self.assertEqual(
            general_admission.regular_registration_proof,
            [self.file_uuids['attestation_inscription_reguliere']],
        )
        self.assertEqual(general_admission.is_external_modification, False)
        self.assertEqual(general_admission.registration_change_form, [])
        self.assertEqual(general_admission.modified_at, datetime.datetime.today())
        self.assertEqual(general_admission.last_update_author, self.sic_manager_user.person)
        self.assertIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            general_admission.requested_documents,
        )

        # With data -> modification
        response = self.client.post(
            url,
            data={
                'poste_diplomatique': self.diplomatic_post.code,
                'est_non_resident_au_sens_decret': False,
                'est_bachelier_belge': True,
                'est_modification_inscription_externe': True,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': False,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(general_admission.diplomatic_post, None)
        self.assertEqual(general_admission.is_non_resident, False)
        self.assertEqual(general_admission.is_belgian_bachelor, True)
        self.assertEqual(general_admission.is_external_reorientation, False)
        self.assertEqual(general_admission.regular_registration_proof, [])
        self.assertEqual(general_admission.is_external_modification, True)
        self.assertEqual(
            general_admission.registration_change_form,
            [self.file_uuids['formulaire_modification_inscription']],
        )

        # With data -> modification & reorientation
        response = self.client.post(
            url,
            data={
                'poste_diplomatique': self.diplomatic_post.code,
                'est_non_resident_au_sens_decret': False,
                'est_bachelier_belge': True,
                'est_modification_inscription_externe': True,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': True,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']
        self.assertFalse(form.is_valid())

        self.assertIn(
            gettext('You cannot ask for both modification and reorientation at the same time.'),
            form.errors.get('__all__', []),
        )

        # No completed field
        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_non_resident_au_sens_decret', []))

        # The candidate is resident but doesn't choose a belgian bachelor
        response = self.client.post(
            url,
            data={
                'est_non_resident_au_sens_decret': True,
                'est_bachelier_belge': '',
                'est_modification_inscription_externe': False,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': True,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(general_admission.is_non_resident, True)
        self.assertEqual(general_admission.is_belgian_bachelor, None)
        self.assertEqual(general_admission.is_external_reorientation, None)
        self.assertEqual(general_admission.regular_registration_proof, [])
        self.assertEqual(general_admission.is_external_modification, None)
        self.assertEqual(general_admission.registration_change_form, [])

        response = self.client.post(
            url,
            data={
                'est_non_resident_au_sens_decret': True,
                'est_bachelier_belge': False,
                'est_modification_inscription_externe': False,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': True,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(general_admission.is_non_resident, True)
        self.assertEqual(general_admission.is_belgian_bachelor, False)
        self.assertEqual(general_admission.is_external_reorientation, False)
        self.assertEqual(general_admission.regular_registration_proof, [])
        self.assertEqual(general_admission.is_external_modification, False)
        self.assertEqual(general_admission.registration_change_form, [])

        # The candidate is not resident and doesn't complete the belgian bachelor field
        response = self.client.post(
            url,
            data={
                'est_non_resident_au_sens_decret': False,
                'est_bachelier_belge': '',
                'est_modification_inscription_externe': True,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': True,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_bachelier_belge', []))

        # The candidate is not resident and doesn't choose a belgian bachelor
        response = self.client.post(
            url,
            data={
                'est_non_resident_au_sens_decret': False,
                'est_bachelier_belge': False,
                'est_modification_inscription_externe': True,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': True,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(general_admission.is_non_resident, False)
        self.assertEqual(general_admission.is_belgian_bachelor, False)
        self.assertEqual(general_admission.is_external_reorientation, False)
        self.assertEqual(general_admission.regular_registration_proof, [])
        self.assertEqual(general_admission.is_external_modification, False)
        self.assertEqual(general_admission.registration_change_form, [])

        # The candidate is not resident and chooses a belgian bachelor and completes every field
        response = self.client.post(
            url,
            data={
                'est_non_resident_au_sens_decret': False,
                'est_bachelier_belge': True,
                'est_modification_inscription_externe': True,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': False,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(general_admission.is_non_resident, False)
        self.assertEqual(general_admission.is_belgian_bachelor, True)
        self.assertEqual(general_admission.is_external_reorientation, False)
        self.assertEqual(general_admission.regular_registration_proof, [])
        self.assertEqual(general_admission.is_external_modification, True)
        self.assertEqual(
            general_admission.registration_change_form,
            [self.file_uuids['formulaire_modification_inscription']],
        )

        # The candidate is not resident and chooses a belgian bachelor but doesn't complete every field
        response = self.client.post(
            url,
            data={
                'est_non_resident_au_sens_decret': False,
                'est_bachelier_belge': True,
                'est_modification_inscription_externe': '',
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': '',
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_modification_inscription_externe', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_reorientation_inscription_externe', []))

        # The candidate is not resident and chooses a belgian bachelor but doesn't want a reorientation or a
        # modification
        response = self.client.post(
            url,
            data={
                'est_non_resident_au_sens_decret': False,
                'est_bachelier_belge': True,
                'est_modification_inscription_externe': False,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': False,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(general_admission.is_non_resident, False)
        self.assertEqual(general_admission.is_belgian_bachelor, True)
        self.assertEqual(general_admission.is_external_reorientation, False)
        self.assertEqual(general_admission.regular_registration_proof, [])
        self.assertEqual(general_admission.is_external_modification, False)
        self.assertEqual(general_admission.registration_change_form, [])

    def test_general_specific_questions_form_submit_with_a_bachelor_without_quota(self):
        self.client.force_login(self.sic_manager_user)

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.bachelor_training,
            candidate__language=settings.LANGUAGE_CODE_EN,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            determined_academic_year=self.academic_years[1],
            is_non_resident=False,
        )

        url = resolve_url('admission:general-education:update:specific-questions', uuid=general_admission.uuid)
        detail_url = resolve_url('admission:general-education:specific-questions', uuid=general_admission.uuid)

        # With data
        response = self.client.post(
            url,
            data={
                'est_bachelier_belge': True,
                'est_modification_inscription_externe': True,
                'formulaire_modification_inscription_0': [self.file_uuids['formulaire_modification_inscription']],
                'est_reorientation_inscription_externe': False,
                'attestation_inscription_reguliere_0': [self.file_uuids['attestation_inscription_reguliere']],
            },
        )

        self.assertRedirects(response=response, expected_url=detail_url, fetch_redirect_response=False)

        general_admission.refresh_from_db()

        self.assertEqual(general_admission.is_belgian_bachelor, True)
        self.assertEqual(general_admission.is_external_reorientation, False)
        self.assertEqual(general_admission.regular_registration_proof, [])
        self.assertEqual(general_admission.is_external_modification, True)
        self.assertEqual(
            general_admission.registration_change_form,
            [self.file_uuids['formulaire_modification_inscription']],
        )

        # No completed field
        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_bachelier_belge', []))
