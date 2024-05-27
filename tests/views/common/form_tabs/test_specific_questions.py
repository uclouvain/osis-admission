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
from admission.contrib.models import GeneralEducationAdmission, ContinuingEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories.continuing_education import (
    ContinuingEducationTrainingFactory,
    ContinuingEducationAdmissionFactory,
)
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
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.person_address_type import PersonAddressType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import Master120TrainingFactory, EducationGroupYearBachelorFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_address import PersonAddressFactory
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2022-01-01')
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class GeneralSpecificQuestionsFormViewTestCase(TestCase):
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
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, "size": 1},
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


@freezegun.freeze_time('2022-01-01')
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class ContinuingSpecificQuestionsFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium', european_union=True)
        cls.ca_country = CountryFactory(iso_code='CA', european_union=False)

        cls.first_entity = EntityWithVersionFactory()

        cls.training = ContinuingEducationTrainingFactory(
            management_entity=cls.first_entity,
            academic_year=cls.academic_years[0],
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

        # Create users
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_entity).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user

        cls.file_uuids = {
            'copie_titre_sejour': uuid.uuid4(),
            'documents_additionnels': uuid.uuid4(),
        }

    def setUp(self):
        # Mock osis document api
        patcher = mock.patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, 'size': 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: value

        # Create data
        self.continuing_admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            training=self.training,
            candidate__country_of_citizenship=self.be_country,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            determined_academic_year=self.academic_years[1],
            registration_as=ChoixInscriptionATitre.PROFESSIONNEL.name,
            specific_question_answers={
                str(self.specific_questions[0].form_item.uuid): 'test',
            },
            residence_permit=[self.file_uuids['copie_titre_sejour']],
            additional_documents=[self.file_uuids['documents_additionnels']],
            head_office_name='UCL',
            unique_business_number='0123',
            vat_number='TVA123',
            professional_email='test@example.be',
            billing_address_type=ChoixTypeAdresseFacturation.AUTRE.name,
            billing_address_street='Rue de la faculte',
            billing_address_street_number='1',
            billing_address_postal_code='1348',
            billing_address_city='Louvain-la-Neuve',
            billing_address_country=self.be_country,
            billing_address_recipient='recipient@example.be',
            billing_address_postal_box='BP8',
        )

        self.url = resolve_url(
            'admission:continuing-education:update:specific-questions',
            uuid=self.continuing_admission.uuid,
        )
        self.details_url = resolve_url(
            'admission:continuing-education:specific-questions',
            uuid=self.continuing_admission.uuid,
        )

    def test_continuing_specific_questions_access(self):
        # If the user is not authenticated, he should be redirected to the login page
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, he should be able to access the page
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_continuing_specific_questions_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form['copie_titre_sejour'].value(), ['foobar'])
        self.assertEqual(form['inscription_a_titre'].value(), ChoixInscriptionATitre.PROFESSIONNEL.name)
        self.assertEqual(form['nom_siege_social'].value(), 'UCL')
        self.assertEqual(form['numero_unique_entreprise'].value(), '0123')
        self.assertEqual(form['numero_tva_entreprise'].value(), 'TVA123')
        self.assertEqual(form['adresse_mail_professionnelle'].value(), 'test@example.be')
        self.assertEqual(form['type_adresse_facturation'].value(), ChoixTypeAdresseFacturation.AUTRE.name)
        self.assertEqual(form['adresse_facturation_destinataire'].value(), 'recipient@example.be')
        self.assertEqual(form['documents_additionnels'].value(), ['foobar'])
        self.assertEqual(
            form['reponses_questions_specifiques'].value(),
            {
                str(self.specific_questions[0].form_item.uuid): 'test',
            },
        )
        self.assertEqual(form['street'].value(), 'Rue de la faculte')
        self.assertEqual(form['street_number'].value(), '1')
        self.assertEqual(form['postal_box'].value(), 'BP8')
        self.assertEqual(form['postal_code'].value(), '1348')
        self.assertEqual(form['city'].value(), 'Louvain-la-Neuve')
        self.assertEqual(form['country'].value(), 'BE')
        self.assertEqual(form['be_postal_code'].value(), '1348')
        self.assertEqual(form['be_city'].value(), 'Louvain-la-Neuve')
        self.assertEqual(form.fields['be_city'].widget.choices, [('Louvain-la-Neuve', 'Louvain-la-Neuve')])
        self.assertEqual(form.display_residence_permit_question, False)

        # With a foreign billing address
        self.continuing_admission.billing_address_country = self.ca_country
        self.continuing_admission.save()

        # With a candidate with a not UE+5 nationality
        self.continuing_admission.candidate.country_of_citizenship = self.ca_country
        self.continuing_admission.candidate.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form['city'].value(), 'Louvain-la-Neuve')
        self.assertEqual(form['country'].value(), 'CA')
        self.assertEqual(form['be_postal_code'].value(), None)
        self.assertEqual(form['be_city'].value(), None)
        self.assertEqual(form.fields['be_city'].widget.choices, [])
        self.assertEqual(form.display_residence_permit_question, True)

    def _assert_fields_are_required(self, form, fields):
        self.assertEqual(len(form.errors), len(fields))
        for field in fields:
            self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get(field, []), 'Field {} must be required'.format(field))

    def test_continuing_specific_questions_form_submission_with_invalid_data(self):
        self.client.force_login(self.sic_manager_user)

        # No data
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self._assert_fields_are_required(form, ['inscription_a_titre'])

        # Missing data for a professional enrolment
        response = self.client.post(
            self.url,
            data={
                'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)

        self._assert_fields_are_required(
            form,
            [
                'nom_siege_social',
                'numero_unique_entreprise',
                'numero_tva_entreprise',
                'adresse_mail_professionnelle',
                'type_adresse_facturation',
            ],
        )

        # Missing data for the custom billing address
        default_data = {
            'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
            'nom_siege_social': 'UCL',
            'numero_unique_entreprise': '0123',
            'numero_tva_entreprise': 'TVA123',
            'adresse_mail_professionnelle': 'test@example.be',
            'type_adresse_facturation': ChoixTypeAdresseFacturation.AUTRE.name,
        }

        # With no data
        response = self.client.post(
            self.url,
            data=default_data,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)

        self._assert_fields_are_required(
            form,
            [
                'street',
                'street_number',
                'city',
                'postal_code',
                'country',
            ],
        )

        # With a local billing address
        response = self.client.post(
            self.url,
            data={
                **default_data,
                'country': self.be_country.iso_code,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)

        self._assert_fields_are_required(form, ['be_city', 'be_postal_code', 'street_number', 'street'])

        # With a foreign billing address
        response = self.client.post(
            self.url,
            data={
                **default_data,
                'country': self.ca_country.iso_code,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)

        self._assert_fields_are_required(form, ['city', 'postal_code', 'street_number', 'street'])

    def test_continuing_specific_questions_form_submission_with_valid_data_for_a_private_enrolment(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.url,
            data={
                'copie_titre_sejour_0': [self.file_uuids['copie_titre_sejour']],
                'inscription_a_titre': ChoixInscriptionATitre.PRIVE.name,
                'reponses_questions_specifiques_0': 'my answer',
                'documents_additionnels_0': [self.file_uuids['documents_additionnels']],
                # Additional data that will be cleaned
                'nom_siege_social': 'Mons',
                'numero_unique_entreprise': '321',
                'numero_tva_entreprise': 'TVA321',
                'adresse_mail_professionnelle': 'other.email@example.be',
                'country': self.be_country.iso_code,
                'street': 'Rue de la paix',
                'street_number': '2',
                'postal_box': 'BP7',
                'be_city': 'Mons',
                'be_postal_code': '4000',
                'city': 'Montreal',
                'postal_code': 'G1R 0B8',
                'adresse_facturation_destinataire': 'other.recipient@example.be',
            },
        )

        self.assertRedirects(response=response, expected_url=self.details_url)

        # Check the admission has been saved
        self.continuing_admission.refresh_from_db()

        self.assertEqual(self.continuing_admission.residence_permit, [])
        self.assertEqual(self.continuing_admission.additional_documents, [self.file_uuids['documents_additionnels']])
        self.assertEqual(self.continuing_admission.registration_as, ChoixInscriptionATitre.PRIVE.name)
        self.assertEqual(self.continuing_admission.head_office_name, '')
        self.assertEqual(self.continuing_admission.unique_business_number, '')
        self.assertEqual(self.continuing_admission.vat_number, '')
        self.assertEqual(self.continuing_admission.professional_email, '')
        self.assertEqual(self.continuing_admission.billing_address_type, '')
        self.assertEqual(self.continuing_admission.billing_address_street, '')
        self.assertEqual(self.continuing_admission.billing_address_street_number, '')
        self.assertEqual(self.continuing_admission.billing_address_postal_code, '')
        self.assertEqual(self.continuing_admission.billing_address_city, '')
        self.assertEqual(self.continuing_admission.billing_address_country, None)
        self.assertEqual(self.continuing_admission.billing_address_recipient, '')
        self.assertEqual(self.continuing_admission.billing_address_postal_box, '')
        self.assertEqual(
            self.continuing_admission.specific_question_answers,
            {
                str(self.specific_questions[0].form_item.uuid): 'my answer',
            },
        )

    def test_continuing_specific_questions_form_submission_with_valid_data_for_a_professional_enrolment(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.url,
            data={
                'copie_titre_sejour_0': [self.file_uuids['copie_titre_sejour']],
                'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                'reponses_questions_specifiques_0': 'my answer',
                'documents_additionnels_0': [self.file_uuids['documents_additionnels']],
                'type_adresse_facturation': ChoixTypeAdresseFacturation.CONTACT.name,
                'nom_siege_social': 'Mons',
                'numero_unique_entreprise': '321',
                'numero_tva_entreprise': 'TVA321',
                'adresse_mail_professionnelle': 'other.email@example.be',
                # Additional data that will be cleaned
                'country': self.be_country.iso_code,
                'street': 'Rue de la paix',
                'street_number': '2',
                'postal_box': 'BP7',
                'be_city': 'Mons',
                'be_postal_code': '4000',
                'city': 'Montreal',
                'postal_code': 'G1R 0B8',
                'adresse_facturation_destinataire': 'other.recipient@example.be',
            },
        )

        self.assertRedirects(response=response, expected_url=self.details_url)

        # Check the admission has been saved
        self.continuing_admission.refresh_from_db()

        self.assertEqual(self.continuing_admission.residence_permit, [])
        self.assertEqual(self.continuing_admission.additional_documents, [self.file_uuids['documents_additionnels']])
        self.assertEqual(self.continuing_admission.registration_as, ChoixInscriptionATitre.PROFESSIONNEL.name)
        self.assertEqual(self.continuing_admission.head_office_name, 'Mons')
        self.assertEqual(self.continuing_admission.unique_business_number, '321')
        self.assertEqual(self.continuing_admission.vat_number, 'TVA321')
        self.assertEqual(self.continuing_admission.professional_email, 'other.email@example.be')
        self.assertEqual(self.continuing_admission.billing_address_type, ChoixTypeAdresseFacturation.CONTACT.name)
        self.assertEqual(self.continuing_admission.billing_address_street, '')
        self.assertEqual(self.continuing_admission.billing_address_street_number, '')
        self.assertEqual(self.continuing_admission.billing_address_postal_code, '')
        self.assertEqual(self.continuing_admission.billing_address_city, '')
        self.assertEqual(self.continuing_admission.billing_address_country, None)
        self.assertEqual(self.continuing_admission.billing_address_recipient, '')
        self.assertEqual(self.continuing_admission.billing_address_postal_box, '')
        self.assertEqual(
            self.continuing_admission.specific_question_answers,
            {
                str(self.specific_questions[0].form_item.uuid): 'my answer',
            },
        )

        # With a local custom billing address
        response = self.client.post(
            self.url,
            data={
                'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                'type_adresse_facturation': ChoixTypeAdresseFacturation.AUTRE.name,
                'nom_siege_social': 'Mons',
                'numero_unique_entreprise': '321',
                'numero_tva_entreprise': 'TVA321',
                'adresse_mail_professionnelle': 'other.email@example.be',
                'country': self.be_country.iso_code,
                'street': 'Rue de la paix',
                'street_number': '2',
                'postal_box': 'BP7',
                'be_city': 'Mons',
                'be_postal_code': '4000',
                'adresse_facturation_destinataire': 'other.recipient@example.be',
            },
        )

        self.assertRedirects(response=response, expected_url=self.details_url)

        # Check the admission has been saved
        self.continuing_admission.refresh_from_db()

        self.assertEqual(self.continuing_admission.residence_permit, [])
        self.assertEqual(self.continuing_admission.additional_documents, [])
        self.assertEqual(self.continuing_admission.registration_as, ChoixInscriptionATitre.PROFESSIONNEL.name)
        self.assertEqual(self.continuing_admission.head_office_name, 'Mons')
        self.assertEqual(self.continuing_admission.unique_business_number, '321')
        self.assertEqual(self.continuing_admission.vat_number, 'TVA321')
        self.assertEqual(self.continuing_admission.professional_email, 'other.email@example.be')
        self.assertEqual(self.continuing_admission.billing_address_type, ChoixTypeAdresseFacturation.AUTRE.name)
        self.assertEqual(self.continuing_admission.billing_address_street, 'Rue de la paix')
        self.assertEqual(self.continuing_admission.billing_address_street_number, '2')
        self.assertEqual(self.continuing_admission.billing_address_postal_code, '4000')
        self.assertEqual(self.continuing_admission.billing_address_city, 'Mons')
        self.assertEqual(self.continuing_admission.billing_address_country, self.be_country)
        self.assertEqual(self.continuing_admission.billing_address_recipient, 'other.recipient@example.be')
        self.assertEqual(self.continuing_admission.billing_address_postal_box, 'BP7')
        self.assertEqual(
            self.continuing_admission.specific_question_answers,
            {
                str(self.specific_questions[0].form_item.uuid): '',
            },
        )

        # With a foreign custom billing address
        response = self.client.post(
            self.url,
            data={
                'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                'type_adresse_facturation': ChoixTypeAdresseFacturation.AUTRE.name,
                'nom_siege_social': 'Mons',
                'numero_unique_entreprise': '321',
                'numero_tva_entreprise': 'TVA321',
                'adresse_mail_professionnelle': 'other.email@example.be',
                'country': self.ca_country.iso_code,
                'street': 'Rue de la paix',
                'street_number': '2',
                'postal_box': 'BP7',
                'city': 'Montreal',
                'postal_code': 'H2Y 3B9',
                'adresse_facturation_destinataire': 'other.recipient@example.be',
            },
        )

        self.assertRedirects(response=response, expected_url=self.details_url)

        # Check the admission has been saved
        self.continuing_admission.refresh_from_db()

        self.assertEqual(self.continuing_admission.residence_permit, [])
        self.assertEqual(self.continuing_admission.additional_documents, [])
        self.assertEqual(self.continuing_admission.registration_as, ChoixInscriptionATitre.PROFESSIONNEL.name)
        self.assertEqual(self.continuing_admission.head_office_name, 'Mons')
        self.assertEqual(self.continuing_admission.unique_business_number, '321')
        self.assertEqual(self.continuing_admission.vat_number, 'TVA321')
        self.assertEqual(self.continuing_admission.professional_email, 'other.email@example.be')
        self.assertEqual(self.continuing_admission.billing_address_type, ChoixTypeAdresseFacturation.AUTRE.name)
        self.assertEqual(self.continuing_admission.billing_address_street, 'Rue de la paix')
        self.assertEqual(self.continuing_admission.billing_address_street_number, '2')
        self.assertEqual(self.continuing_admission.billing_address_postal_code, 'H2Y 3B9')
        self.assertEqual(self.continuing_admission.billing_address_city, 'Montreal')
        self.assertEqual(self.continuing_admission.billing_address_country, self.ca_country)
        self.assertEqual(self.continuing_admission.billing_address_recipient, 'other.recipient@example.be')
        self.assertEqual(self.continuing_admission.billing_address_postal_box, 'BP7')
        self.assertEqual(
            self.continuing_admission.specific_question_answers,
            {
                str(self.specific_questions[0].form_item.uuid): '',
            },
        )

    def test_continuing_specific_questions_form_submission_with_valid_data_for_a_not_hue5_candidate(self):
        self.client.force_login(self.sic_manager_user)

        self.continuing_admission.candidate.country_of_citizenship = self.ca_country
        self.continuing_admission.candidate.save()

        response = self.client.post(
            self.url,
            data={
                'copie_titre_sejour_0': [self.file_uuids['copie_titre_sejour']],
                'inscription_a_titre': ChoixInscriptionATitre.PRIVE.name,
            },
        )

        self.assertRedirects(response=response, expected_url=self.details_url)

        # Check the admission has been saved
        self.continuing_admission.refresh_from_db()

        self.assertEqual(self.continuing_admission.residence_permit, [self.file_uuids['copie_titre_sejour']])
        self.assertEqual(self.continuing_admission.registration_as, ChoixInscriptionATitre.PRIVE.name)
        self.assertEqual(self.continuing_admission.last_update_author, self.sic_manager_user.person)
