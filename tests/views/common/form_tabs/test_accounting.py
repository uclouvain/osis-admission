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
from rest_framework import status

from admission.contrib.models import Accounting
from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums import (
    TypeSituationAssimilation,
    ChoixAffiliationSport,
    ChoixTypeCompteBancaire,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    LienParente,
    ChoixAssimilation6,
)
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.forms.admission.accounting import AccountingForm
from admission.tests.factories.curriculum import EducationalExperienceYearFactory, EducationalExperienceFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory, CandidateFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.campus import Campus
from base.models.enums.community import CommunityEnum
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from program_management.models.education_group_version import EducationGroupVersion
from reference.services.iban_validator import IBANValidatorException, IBANValidatorRequestException
from reference.tests.factories.country import CountryFactory


def validate_with_no_service_exception(value):
    raise IBANValidatorRequestException()


def validate_with_invalid_iban_exception(value):
    raise IBANValidatorException('Invalid IBAN')


def validate_ok(value):
    return True


@freezegun.freeze_time('2023-01-01')
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class GeneralAccountingFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]
        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        cls.louvain_campus = Campus.objects.get(external_id=CampusFactory(name='Louvain-la-Neuve').external_id)
        cls.other_campus = Campus.objects.get(external_id=CampusFactory(name='Other').external_id)
        EntityVersionFactory(entity=cls.first_doctoral_commission)
        cls.default_form_data = {
            'demande_allocation_d_etudes_communaute_francaise_belgique': 'False',
            'enfant_personnel': 'False',
            'type_situation_assimilation': TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
            'etudiant_solidaire': 'False',
            'type_numero_compte': ChoixTypeCompteBancaire.NON.name,
            'affiliation_sport': ChoixAffiliationSport.NON.name,
        }
        cls.files_uuids = {
            file_field: [uuid.uuid4()]
            for file_field in AccountingForm.ASSIMILATION_FILE_FIELDS
            + [
                'attestation_absence_dette_etablissement',
                'attestation_enfant_personnel',
            ]
        }

    def setUp(self):
        # Create data
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_doctoral_commission,
            training__academic_year=self.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            candidate__id_photo=[],
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Create users
        self.sic_manager_user = SicManagementRoleFactory(entity=self.first_doctoral_commission).person.user
        self.program_manager_user = ProgramManagerRoleFactory(
            education_group=self.general_admission.training.education_group,
        ).person.user

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

        # Mock iban validator
        iban_validator_patcher = mock.patch("reference.services.iban_validator.IBANValidatorService.validate")
        self.mock_iban_validator = iban_validator_patcher.start()
        self.mock_iban_validator.side_effect = validate_ok
        self.addCleanup(iban_validator_patcher.stop)

        # Targeted url
        self.form_url = resolve_url('admission:general-education:update:accounting', uuid=self.general_admission.uuid)
        self.detail_url = resolve_url('admission:general-education:accounting', uuid=self.general_admission.uuid)

    def _assert_missing_fields(self, form, missing_fields):
        """Assert that all specified fields are missing in the form."""
        self.assertEqual(len(form.errors), len(missing_fields))
        for field in missing_fields:
            self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get(field, []))

    def test_general_accounting_access(self):
        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.form_url, fetch_redirect_response=False)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_general_accounting_form_initialization(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)
        self.assertEqual(response.context['formatted_relationship'], None)
        self.assertEqual(response.context['with_assimilation'], True)
        self.assertEqual(response.context['is_general'], True)

        accounting = response.context['accounting']
        self.assertEqual(accounting['demande_allocation_d_etudes_communaute_francaise_belgique'], False)
        self.assertEqual(accounting['enfant_personnel'], False)
        self.assertEqual(accounting['type_situation_assimilation'], TypeSituationAssimilation.AUCUNE_ASSIMILATION.name)
        self.assertEqual(accounting['affiliation_sport'], ChoixAffiliationSport.NON.name)
        self.assertEqual(accounting['etudiant_solidaire'], False)
        self.assertEqual(accounting['type_numero_compte'], ChoixTypeCompteBancaire.NON.name)

        self.assertEqual(accounting['derniers_etablissements_superieurs_communaute_fr_frequentes'], None)

        # Check form initialization
        form = response.context['form']

        self.assertEqual(form.fields['demande_allocation_d_etudes_communaute_francaise_belgique'].required, True)
        self.assertEqual(form.fields['enfant_personnel'].required, True)
        self.assertEqual(form.fields['affiliation_sport'].required, True)
        self.assertEqual(form.display_sport_question, True)
        self.assertEqual(
            form.fields['affiliation_sport'].choices,
            [
                (ChoixAffiliationSport.LOUVAIN_WOLUWE.name, ChoixAffiliationSport.LOUVAIN_WOLUWE.value),
                (ChoixAffiliationSport.NON.name, ChoixAffiliationSport.NON.value),
            ],
        )
        self.assertEqual(form.fields['type_situation_assimilation'].required, True)

    def test_general_accounting_form_initialization_with_previous_experiences(self):
        self.client.force_login(self.sic_manager_user)

        # Add a first experience -> change the label of the related field
        current_year = get_current_year()
        first_experience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            obtained_diploma=False,
            country=self.be_country,
            institute=OrganizationFactory(
                community=CommunityEnum.FRENCH_SPEAKING.name,
                acronym='INSTITUTE',
                name='First institute',
            ),
        )
        EducationalExperienceYearFactory(
            educational_experience=first_experience,
            academic_year=AcademicYearFactory(year=current_year),
        )

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form initialization
        form = response.context['form']
        self.assertEqual(
            form.fields['attestation_absence_dette_etablissement'].label,
            "Attestation stipulant l'absence de dettes vis-à-vis de l'établissement "
            "fréquenté durant l'année académique 2022-2023 : First institute.",
        )

        # Add a second experience -> change the label of the related field
        second_experience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            obtained_diploma=False,
            country=self.be_country,
            institute=OrganizationFactory(
                community=CommunityEnum.FRENCH_SPEAKING.name,
                acronym='INSTITUTE',
                name='Third institute',
            ),
        )
        EducationalExperienceYearFactory(
            educational_experience=second_experience,
            academic_year=AcademicYearFactory(year=current_year),
        )

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form initialization
        form = response.context['form']

        common_sentence = (
            "Attestations stipulant l'absence de dettes vis-à-vis des établissements fréquentés durant "
            "l'année académique 2022-2023 : "
        )

        self.assertIn(
            form.fields['attestation_absence_dette_etablissement'].label,
            {
                common_sentence + 'First institute, Third institute.',
                common_sentence + 'Third institute, First institute.',
            },
        )

    def test_general_accounting_form_initialization_with_other_campus(self):
        self.client.force_login(self.sic_manager_user)

        # Change teaching campus -> this one has no sport pass so we don't display the related question
        education_group_version = EducationGroupVersion.objects.get(offer=self.general_admission.training)
        education_group_version.root_group.main_teaching_campus = self.other_campus
        education_group_version.root_group.save()

        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form initialization
        form = response.context['form']

        self.assertEqual(
            form.fields['affiliation_sport'].choices,
            [(ChoixAffiliationSport.NON.name, ChoixAffiliationSport.NON.value)],
        )
        self.assertEqual(form.fields['affiliation_sport'].required, False)
        self.assertEqual(form.display_sport_question, False)

    def test_general_accounting_form_initialization_without_assimilation(self):
        self.client.force_login(self.sic_manager_user)

        # No country of citizenship -> no assimilation
        self.general_admission.candidate.country_of_citizenship = None
        self.general_admission.candidate.save()

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form initialization
        form = response.context['form']
        self.assertEqual(form.fields['type_situation_assimilation'].required, False)

        # Country of citizenship in European Union -> no assimilation
        self.general_admission.candidate.country_of_citizenship = CountryFactory(european_union=True)
        self.general_admission.candidate.save()

        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form initialization
        form = response.context['form']
        self.assertEqual(form.fields['type_situation_assimilation'].required, False)

    def test_post_general_accounting_form_with_no_data(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(self.form_url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']

        self.assertFalse(form.is_valid())

        self._assert_missing_fields(
            form,
            [
                'demande_allocation_d_etudes_communaute_francaise_belgique',
                'enfant_personnel',
                'type_situation_assimilation',
                'etudiant_solidaire',
                'type_numero_compte',
                'affiliation_sport',
            ],
        )

    def test_post_general_accounting_form(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.post(
            self.form_url,
            data={
                **self.default_form_data,
                'attestation_enfant_personnel_0': self.files_uuids['attestation_enfant_personnel'][0],
                'attestation_absence_dette_etablissement_0': self.files_uuids[
                    'attestation_absence_dette_etablissement'
                ][0],
                'numero_compte_iban': 'BE43068999999501',
                'numero_compte_autre_format': '123456',
                'code_bic_swift_banque': 'GKCCBEBB',
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check admission updates
        self.general_admission.refresh_from_db()
        accounting: Accounting = self.general_admission.accounting

        self.assertEqual(accounting.institute_absence_debts_certificate, [])
        self.assertEqual(accounting.french_community_study_allowance_application, False)
        self.assertEqual(accounting.is_staff_child, False)
        self.assertEqual(accounting.staff_child_certificate, [])
        self.assertEqual(accounting.assimilation_situation, TypeSituationAssimilation.AUCUNE_ASSIMILATION.name)
        self.assertEqual(accounting.solidarity_student, False)
        self.assertEqual(accounting.account_number_type, ChoixTypeCompteBancaire.NON.name)
        self.assertEqual(accounting.iban_account_number, '')
        self.assertEqual(accounting.other_format_account_number, '')
        self.assertEqual(accounting.bic_swift_code, '')
        self.assertEqual(accounting.account_holder_first_name, '')
        self.assertEqual(accounting.account_holder_last_name, '')
        self.assertEqual(accounting.sport_affiliation, ChoixAffiliationSport.NON.name)
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())
        self.assertIn(
            f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
            self.general_admission.requested_documents,
        )

    def test_post_general_accounting_form_with_iban_number(self):
        self.client.force_login(self.sic_manager_user)

        # Missing data
        response = self.client.post(
            self.form_url,
            data={
                **self.default_form_data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self._assert_missing_fields(
            form,
            [
                'numero_compte_iban',
                'prenom_titulaire_compte',
                'nom_titulaire_compte',
            ],
        )

        # Valid data
        response = self.client.post(
            self.form_url,
            data={
                **self.default_form_data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
                'numero_compte_autre_format': '123456',
                'code_bic_swift_banque': 'GKCCBEBB',
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check admission updates
        accounting: Accounting = self.general_admission.accounting

        self.assertEqual(accounting.account_number_type, ChoixTypeCompteBancaire.IBAN.name)
        self.assertEqual(accounting.iban_account_number, 'BE43068999999501')
        self.assertEqual(accounting.other_format_account_number, '')
        self.assertEqual(accounting.bic_swift_code, '')
        self.assertEqual(accounting.account_holder_first_name, 'John')
        self.assertEqual(accounting.account_holder_last_name, 'Doe')
        self.assertEqual(accounting.valid_iban, True)

        # Invalid IBAN
        self.mock_iban_validator.side_effect = validate_with_invalid_iban_exception
        response = self.client.post(
            self.form_url,
            data={
                **self.default_form_data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
            },
        )

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid IBAN', form.errors.get('numero_compte_iban', []))

        # An error occured when checking the IBAN
        self.mock_iban_validator.side_effect = validate_with_no_service_exception
        response = self.client.post(
            self.form_url,
            data={
                **self.default_form_data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting updates
        accounting.refresh_from_db()
        self.assertEqual(accounting.valid_iban, None)

    def test_post_general_accounting_form_with_other_account_number(self):
        self.client.force_login(self.sic_manager_user)

        # Missing data
        response = self.client.post(
            self.form_url,
            data={
                **self.default_form_data,
                'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self._assert_missing_fields(
            form,
            [
                'numero_compte_autre_format',
                'code_bic_swift_banque',
                'prenom_titulaire_compte',
                'nom_titulaire_compte',
            ],
        )

        # Check response

        # Valid data
        response = self.client.post(
            self.form_url,
            data={
                **self.default_form_data,
                'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
                'numero_compte_iban': 'BE43068999999501',
                'numero_compte_autre_format': '123456',
                'code_bic_swift_banque': 'GKCCBEBB',
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check admission updates
        accounting: Accounting = self.general_admission.accounting

        self.assertEqual(accounting.account_number_type, ChoixTypeCompteBancaire.AUTRE_FORMAT.name)
        self.assertEqual(accounting.iban_account_number, '')
        self.assertEqual(accounting.other_format_account_number, '123456')
        self.assertEqual(accounting.bic_swift_code, 'GKCCBEBB')
        self.assertEqual(accounting.account_holder_first_name, 'John')
        self.assertEqual(accounting.account_holder_last_name, 'Doe')

    def test_post_general_accounting_form_with_first_assimilation(self):
        self.client.force_login(self.sic_manager_user)

        assimilation_data = {
            **self.default_form_data,
            'type_situation_assimilation': (
                TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name
            ),
            'carte_resident_longue_duree_0': self.files_uuids['carte_resident_longue_duree'][0],
            'carte_cire_sejour_illimite_etranger_0': self.files_uuids['carte_cire_sejour_illimite_etranger'][0],
            'carte_sejour_membre_ue_0': self.files_uuids['carte_sejour_membre_ue'][0],
            'carte_sejour_permanent_membre_ue_0': self.files_uuids['carte_sejour_permanent_membre_ue'][0],
        }

        # Missing data
        response = self.client.post(self.form_url, data=assimilation_data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']
        self.assertFalse(form.is_valid())

        self._assert_missing_fields(form, ['sous_type_situation_assimilation_1'])

        # TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting = self.general_admission.accounting

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name,
        )
        self.assertEqual(
            accounting.assimilation_1_situation_type,
            ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE.name,
        )
        self.assertEqual(accounting.long_term_resident_card, self.files_uuids['carte_resident_longue_duree'])
        self.assertEqual(accounting.cire_unlimited_stay_foreigner_card, [])
        self.assertEqual(accounting.ue_family_member_residence_card, [])
        self.assertEqual(accounting.ue_family_member_permanent_residence_card, [])

        # TITULAIRE_CARTE_ETRANGER
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name,
        )
        self.assertEqual(
            accounting.assimilation_1_situation_type,
            ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
        )
        self.assertEqual(accounting.long_term_resident_card, [])
        self.assertEqual(
            accounting.cire_unlimited_stay_foreigner_card,
            self.files_uuids['carte_cire_sejour_illimite_etranger'],
        )
        self.assertEqual(accounting.ue_family_member_residence_card, [])
        self.assertEqual(accounting.ue_family_member_permanent_residence_card, [])

        # TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_1': (
                    ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE.name
                ),
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name,
        )
        self.assertEqual(
            accounting.assimilation_1_situation_type,
            ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE.name,
        )
        self.assertEqual(accounting.long_term_resident_card, [])
        self.assertEqual(accounting.cire_unlimited_stay_foreigner_card, [])
        self.assertEqual(accounting.ue_family_member_residence_card, [])
        self.assertEqual(
            accounting.ue_family_member_permanent_residence_card,
            self.files_uuids['carte_sejour_permanent_membre_ue'],
        )

        # TITULAIRE_CARTE_SEJOUR_MEMBRE_UE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_MEMBRE_UE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name,
        )
        self.assertEqual(
            accounting.assimilation_1_situation_type,
            ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_MEMBRE_UE.name,
        )
        self.assertEqual(accounting.long_term_resident_card, [])
        self.assertEqual(accounting.cire_unlimited_stay_foreigner_card, [])
        self.assertEqual(accounting.ue_family_member_residence_card, self.files_uuids['carte_sejour_membre_ue'])
        self.assertEqual(accounting.ue_family_member_permanent_residence_card, [])

    def test_post_general_accounting_form_with_second_assimilation(self):
        self.client.force_login(self.sic_manager_user)

        assimilation_data = {
            **self.default_form_data,
            'type_situation_assimilation': (
                TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name
            ),
            'carte_a_b_refugie_0': self.files_uuids['carte_a_b_refugie'][0],
            'annexe_25_26_refugies_apatrides_0': self.files_uuids['annexe_25_26_refugies_apatrides'][0],
            'attestation_immatriculation_0': self.files_uuids['attestation_immatriculation'][0],
            'preuve_statut_apatride_0': self.files_uuids['preuve_statut_apatride'][0],
            'carte_a_b_0': self.files_uuids['carte_a_b'][0],
            'decision_protection_subsidiaire_0': self.files_uuids['decision_protection_subsidiaire'][0],
            'decision_protection_temporaire_0': self.files_uuids['decision_protection_temporaire'][0],
            'carte_a_0': self.files_uuids['carte_a'][0],
        }

        # Missing data
        response = self.client.post(self.form_url, data=assimilation_data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']
        self.assertFalse(form.is_valid())

        self._assert_missing_fields(form, ['sous_type_situation_assimilation_2'])

        # REFUGIE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.REFUGIE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting = self.general_admission.accounting

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name,
        )
        self.assertEqual(accounting.assimilation_2_situation_type, ChoixAssimilation2.REFUGIE.name)
        self.assertEqual(accounting.refugee_a_b_card, self.files_uuids['carte_a_b_refugie'])
        self.assertEqual(accounting.refugees_stateless_annex_25_26, [])
        self.assertEqual(accounting.registration_certificate, [])
        self.assertEqual(accounting.stateless_person_proof, [])
        self.assertEqual(accounting.a_b_card, [])
        self.assertEqual(accounting.subsidiary_protection_decision, [])
        self.assertEqual(accounting.temporary_protection_decision, [])
        self.assertEqual(accounting.a_card, [])

        # DEMANDEUR_ASILE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.DEMANDEUR_ASILE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name,
        )
        self.assertEqual(accounting.assimilation_2_situation_type, ChoixAssimilation2.DEMANDEUR_ASILE.name)
        self.assertEqual(accounting.refugee_a_b_card, [])
        self.assertEqual(accounting.refugees_stateless_annex_25_26, self.files_uuids['annexe_25_26_refugies_apatrides'])
        self.assertEqual(accounting.registration_certificate, self.files_uuids['attestation_immatriculation'])
        self.assertEqual(accounting.stateless_person_proof, [])
        self.assertEqual(accounting.a_b_card, [])
        self.assertEqual(accounting.subsidiary_protection_decision, [])
        self.assertEqual(accounting.temporary_protection_decision, [])
        self.assertEqual(accounting.a_card, [])

        # APATRIDE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.APATRIDE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name,
        )
        self.assertEqual(accounting.assimilation_2_situation_type, ChoixAssimilation2.APATRIDE.name)
        self.assertEqual(accounting.refugee_a_b_card, [])
        self.assertEqual(accounting.refugees_stateless_annex_25_26, [])
        self.assertEqual(accounting.registration_certificate, [])
        self.assertEqual(accounting.stateless_person_proof, self.files_uuids['preuve_statut_apatride'])
        self.assertEqual(accounting.a_b_card, [])
        self.assertEqual(accounting.subsidiary_protection_decision, [])
        self.assertEqual(accounting.temporary_protection_decision, [])
        self.assertEqual(accounting.a_card, [])

        # PROTECTION_SUBSIDIAIRE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name,
        )
        self.assertEqual(accounting.assimilation_2_situation_type, ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name)
        self.assertEqual(accounting.refugee_a_b_card, [])
        self.assertEqual(accounting.refugees_stateless_annex_25_26, [])
        self.assertEqual(accounting.registration_certificate, [])
        self.assertEqual(accounting.stateless_person_proof, [])
        self.assertEqual(accounting.a_b_card, self.files_uuids['carte_a_b'])
        self.assertEqual(accounting.subsidiary_protection_decision, self.files_uuids['decision_protection_subsidiaire'])
        self.assertEqual(accounting.temporary_protection_decision, [])
        self.assertEqual(accounting.a_card, [])

        # PROTECTION_TEMPORAIRE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.PROTECTION_TEMPORAIRE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name,
        )
        self.assertEqual(accounting.assimilation_2_situation_type, ChoixAssimilation2.PROTECTION_TEMPORAIRE.name)
        self.assertEqual(accounting.refugee_a_b_card, [])
        self.assertEqual(accounting.refugees_stateless_annex_25_26, [])
        self.assertEqual(accounting.registration_certificate, [])
        self.assertEqual(accounting.stateless_person_proof, [])
        self.assertEqual(accounting.a_b_card, [])
        self.assertEqual(accounting.subsidiary_protection_decision, [])
        self.assertEqual(accounting.temporary_protection_decision, self.files_uuids['decision_protection_temporaire'])
        self.assertEqual(accounting.a_card, self.files_uuids['carte_a'])

    def test_post_general_accounting_form_with_third_assimilation(self):
        self.client.force_login(self.sic_manager_user)

        assimilation_data = {
            **self.default_form_data,
            'type_situation_assimilation': (
                TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name
            ),
            'titre_sejour_3_mois_professionel_0': self.files_uuids['titre_sejour_3_mois_professionel'][0],
            'fiches_remuneration_0': self.files_uuids['fiches_remuneration'][0],
            'titre_sejour_3_mois_remplacement_0': self.files_uuids['titre_sejour_3_mois_remplacement'][0],
            'preuve_allocations_chomage_pension_indemnite_0': self.files_uuids[
                'preuve_allocations_chomage_pension_indemnite'
            ][0],
        }

        # Missing data
        response = self.client.post(self.form_url, data=assimilation_data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']
        self.assertFalse(form.is_valid())

        self._assert_missing_fields(form, ['sous_type_situation_assimilation_3'])

        # AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_3': (
                    ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name
                ),
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting = self.general_admission.accounting

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name,
        )
        self.assertEqual(
            accounting.assimilation_3_situation_type,
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name,
        )
        self.assertEqual(
            accounting.professional_3_month_residence_permit,
            self.files_uuids['titre_sejour_3_mois_professionel'],
        )
        self.assertEqual(accounting.salary_slips, self.files_uuids['fiches_remuneration'])
        self.assertEqual(accounting.replacement_3_month_residence_permit, [])
        self.assertEqual(accounting.unemployment_benefit_pension_compensation_proof, [])

        # AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_3': (
                    ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name
                ),
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name,
        )
        self.assertEqual(
            accounting.assimilation_3_situation_type,
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name,
        )
        self.assertEqual(accounting.professional_3_month_residence_permit, [])
        self.assertEqual(accounting.salary_slips, [])
        self.assertEqual(
            accounting.replacement_3_month_residence_permit,
            self.files_uuids['titre_sejour_3_mois_remplacement'],
        )
        self.assertEqual(
            accounting.unemployment_benefit_pension_compensation_proof,
            self.files_uuids['preuve_allocations_chomage_pension_indemnite'],
        )

    def test_post_general_accounting_form_with_fourth_assimilation(self):
        self.client.force_login(self.sic_manager_user)

        assimilation_data = {
            **self.default_form_data,
            'type_situation_assimilation': TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            'attestation_cpas_0': self.files_uuids['attestation_cpas'][0],
        }

        response = self.client.post(self.form_url, data=assimilation_data)

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting = self.general_admission.accounting

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
        )
        self.assertEqual(accounting.cpas_certificate, self.files_uuids['attestation_cpas'])

    def test_post_general_accounting_form_with_fifth_assimilation(self):
        self.client.force_login(self.sic_manager_user)

        assimilation_data = {
            **self.default_form_data,
            'type_situation_assimilation': (
                TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name
            ),
            'composition_menage_acte_naissance_0': self.files_uuids['composition_menage_acte_naissance'][0],
            'acte_tutelle_0': self.files_uuids['acte_tutelle'][0],
            'composition_menage_acte_mariage_0': self.files_uuids['composition_menage_acte_mariage'][0],
            'attestation_cohabitation_legale_0': self.files_uuids['attestation_cohabitation_legale'][0],
            'carte_identite_parent_0': self.files_uuids['carte_identite_parent'][0],
            'titre_sejour_longue_duree_parent_0': self.files_uuids['titre_sejour_longue_duree_parent'][0],
            'annexe_25_26_refugies_apatrides_decision_protection_parent_0': self.files_uuids[
                'annexe_25_26_refugies_apatrides_decision_protection_parent'
            ][0],
            'titre_sejour_3_mois_parent_0': self.files_uuids['titre_sejour_3_mois_parent'][0],
            'fiches_remuneration_parent_0': self.files_uuids['fiches_remuneration_parent'][0],
            'attestation_cpas_parent_0': self.files_uuids['attestation_cpas_parent'][0],
        }

        # Missing data
        response = self.client.post(self.form_url, data=assimilation_data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']
        self.assertFalse(form.is_valid())

        self._assert_missing_fields(form, ['sous_type_situation_assimilation_5', 'relation_parente'])

        # PERE & A_NATIONALITE_UE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_5': ChoixAssimilation5.A_NATIONALITE_UE.name,
                'relation_parente': LienParente.PERE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting = self.general_admission.accounting

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name,
        )
        self.assertEqual(accounting.assimilation_5_situation_type, ChoixAssimilation5.A_NATIONALITE_UE.name)
        self.assertEqual(accounting.relationship, LienParente.PERE.name)
        self.assertEqual(
            accounting.household_composition_or_birth_certificate,
            self.files_uuids['composition_menage_acte_naissance'],
        )
        self.assertEqual(accounting.tutorship_act, [])
        self.assertEqual(accounting.household_composition_or_marriage_certificate, [])
        self.assertEqual(accounting.legal_cohabitation_certificate, [])
        self.assertEqual(accounting.parent_identity_card, self.files_uuids['carte_identite_parent'])
        self.assertEqual(accounting.parent_long_term_residence_permit, [])
        self.assertEqual(accounting.parent_refugees_stateless_annex_25_26_or_protection_decision, [])
        self.assertEqual(accounting.parent_3_month_residence_permit, [])
        self.assertEqual(accounting.parent_salary_slips, [])
        self.assertEqual(accounting.parent_cpas_certificate, [])

        # MERE & TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_5': ChoixAssimilation5.TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE.name,
                'relation_parente': LienParente.MERE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name,
        )
        self.assertEqual(
            accounting.assimilation_5_situation_type,
            ChoixAssimilation5.TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE.name,
        )
        self.assertEqual(accounting.relationship, LienParente.MERE.name)
        self.assertEqual(
            accounting.household_composition_or_birth_certificate,
            self.files_uuids['composition_menage_acte_naissance'],
        )
        self.assertEqual(accounting.tutorship_act, [])
        self.assertEqual(accounting.household_composition_or_marriage_certificate, [])
        self.assertEqual(accounting.legal_cohabitation_certificate, [])
        self.assertEqual(accounting.parent_identity_card, [])
        self.assertEqual(
            accounting.parent_long_term_residence_permit,
            self.files_uuids['titre_sejour_longue_duree_parent'],
        )
        self.assertEqual(accounting.parent_refugees_stateless_annex_25_26_or_protection_decision, [])
        self.assertEqual(accounting.parent_3_month_residence_permit, [])
        self.assertEqual(accounting.parent_salary_slips, [])
        self.assertEqual(accounting.parent_cpas_certificate, [])

        # CONJOINT & CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_5': (
                    ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name
                ),
                'relation_parente': LienParente.CONJOINT.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name,
        )
        self.assertEqual(
            accounting.assimilation_5_situation_type,
            ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name,
        )
        self.assertEqual(accounting.relationship, LienParente.CONJOINT.name)
        self.assertEqual(accounting.household_composition_or_birth_certificate, [])
        self.assertEqual(accounting.tutorship_act, [])
        self.assertEqual(
            accounting.household_composition_or_marriage_certificate,
            self.files_uuids['composition_menage_acte_mariage'],
        )
        self.assertEqual(accounting.legal_cohabitation_certificate, [])
        self.assertEqual(accounting.parent_identity_card, [])
        self.assertEqual(accounting.parent_long_term_residence_permit, [])
        self.assertEqual(
            accounting.parent_refugees_stateless_annex_25_26_or_protection_decision,
            self.files_uuids['annexe_25_26_refugies_apatrides_decision_protection_parent'],
        )
        self.assertEqual(accounting.parent_3_month_residence_permit, [])
        self.assertEqual(accounting.parent_salary_slips, [])
        self.assertEqual(accounting.parent_cpas_certificate, [])

        # TUTEUR_LEGAL & AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_5': (
                    ChoixAssimilation5.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name
                ),
                'relation_parente': LienParente.TUTEUR_LEGAL.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name,
        )
        self.assertEqual(
            accounting.assimilation_5_situation_type,
            ChoixAssimilation5.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name,
        )
        self.assertEqual(accounting.relationship, LienParente.TUTEUR_LEGAL.name)
        self.assertEqual(accounting.household_composition_or_birth_certificate, [])
        self.assertEqual(accounting.tutorship_act, self.files_uuids['acte_tutelle'])
        self.assertEqual(accounting.household_composition_or_marriage_certificate, [])
        self.assertEqual(accounting.legal_cohabitation_certificate, [])
        self.assertEqual(accounting.parent_identity_card, [])
        self.assertEqual(accounting.parent_long_term_residence_permit, [])
        self.assertEqual(accounting.parent_refugees_stateless_annex_25_26_or_protection_decision, [])
        self.assertEqual(accounting.parent_3_month_residence_permit, self.files_uuids['titre_sejour_3_mois_parent'])
        self.assertEqual(accounting.parent_salary_slips, self.files_uuids['fiches_remuneration_parent'])
        self.assertEqual(accounting.parent_cpas_certificate, [])

        # COHABITANT_LEGAL & PRIS_EN_CHARGE_OU_DESIGNE_CPAS
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_5': ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
                'relation_parente': LienParente.COHABITANT_LEGAL.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name,
        )
        self.assertEqual(
            accounting.assimilation_5_situation_type,
            ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
        )
        self.assertEqual(accounting.relationship, LienParente.COHABITANT_LEGAL.name)
        self.assertEqual(accounting.household_composition_or_birth_certificate, [])
        self.assertEqual(accounting.tutorship_act, [])
        self.assertEqual(accounting.household_composition_or_marriage_certificate, [])
        self.assertEqual(accounting.legal_cohabitation_certificate, self.files_uuids['attestation_cohabitation_legale'])
        self.assertEqual(accounting.parent_identity_card, [])
        self.assertEqual(accounting.parent_long_term_residence_permit, [])
        self.assertEqual(accounting.parent_refugees_stateless_annex_25_26_or_protection_decision, [])
        self.assertEqual(accounting.parent_3_month_residence_permit, [])
        self.assertEqual(accounting.parent_salary_slips, [])
        self.assertEqual(accounting.parent_cpas_certificate, self.files_uuids['attestation_cpas_parent'])

    def test_post_general_accounting_form_with_sixth_assimilation(self):
        self.client.force_login(self.sic_manager_user)

        assimilation_data = {
            **self.default_form_data,
            'type_situation_assimilation': TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name,
            'decision_bourse_cfwb_0': self.files_uuids['decision_bourse_cfwb'][0],
            'attestation_boursier_0': self.files_uuids['attestation_boursier'][0],
        }

        # Missing data
        response = self.client.post(self.form_url, data=assimilation_data)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check form
        form = response.context['form']
        self.assertFalse(form.is_valid())

        self._assert_missing_fields(form, ['sous_type_situation_assimilation_6'])

        # A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting = self.general_admission.accounting

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name,
        )
        self.assertEqual(
            accounting.assimilation_6_situation_type,
            ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE.name,
        )
        self.assertEqual(accounting.cfwb_scholarship_decision, self.files_uuids['decision_bourse_cfwb'])
        self.assertEqual(accounting.scholarship_certificate, [])

        # A_BOURSE_COOPERATION_DEVELOPPEMENT
        response = self.client.post(
            self.form_url,
            data={
                **assimilation_data,
                'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
            },
        )

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting.refresh_from_db()

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name,
        )
        self.assertEqual(
            accounting.assimilation_6_situation_type,
            ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
        )
        self.assertEqual(accounting.cfwb_scholarship_decision, [])
        self.assertEqual(accounting.scholarship_certificate, self.files_uuids['attestation_boursier'])

    def test_post_general_accounting_form_with_seventh_assimilation(self):
        self.client.force_login(self.sic_manager_user)

        assimilation_data = {
            **self.default_form_data,
            'type_situation_assimilation': TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE.name,
            'titre_identite_sejour_longue_duree_ue_0': self.files_uuids['titre_identite_sejour_longue_duree_ue'][0],
            'titre_sejour_belgique_0': self.files_uuids['titre_sejour_belgique'][0],
        }

        response = self.client.post(self.form_url, data=assimilation_data)

        # Check response
        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)

        # Check accounting data
        accounting = self.general_admission.accounting

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE.name,
        )
        self.assertEqual(
            accounting.ue_long_term_stay_identity_document,
            self.files_uuids['titre_identite_sejour_longue_duree_ue'],
        )
        self.assertEqual(accounting.belgium_residence_permit, self.files_uuids['titre_sejour_belgique'])
