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

import uuid
from unittest.mock import patch

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from rest_framework.test import APITestCase

from admission.contrib.models import Accounting
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums import (
    ChoixAffiliationSport,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixTypeCompteBancaire,
    LienParente,
    TypeSituationAssimilation,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.accounting import AccountingFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.models.enums.community import CommunityEnum
from base.models.enums.entity_type import EntityType
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from osis_profile.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from reference.tests.factories.country import CountryFactory

doctorate_file_fields = [
    ['institute_absence_debts_certificate', 'attestation_absence_dette_etablissement'],
    ['long_term_resident_card', 'carte_resident_longue_duree'],
    ['cire_unlimited_stay_foreigner_card', 'carte_cire_sejour_illimite_etranger'],
    ['ue_family_member_residence_card', 'carte_sejour_membre_ue'],
    ['ue_family_member_permanent_residence_card', 'carte_sejour_permanent_membre_ue'],
    ['refugee_a_b_card', 'carte_a_b_refugie'],
    ['refugees_stateless_annex_25_26', 'annexe_25_26_refugies_apatrides'],
    ['registration_certificate', 'attestation_immatriculation'],
    ['a_b_card', 'carte_a_b'],
    ['subsidiary_protection_decision', 'decision_protection_subsidiaire'],
    ['temporary_protection_decision', 'decision_protection_temporaire'],
    ['professional_3_month_residence_permit', 'titre_sejour_3_mois_professionel'],
    ['salary_slips', 'fiches_remuneration'],
    ['replacement_3_month_residence_permit', 'titre_sejour_3_mois_remplacement'],
    ['unemployment_benefit_pension_compensation_proof', 'preuve_allocations_chomage_pension_indemnite'],
    ['cpas_certificate', 'attestation_cpas'],
    ['household_composition_or_birth_certificate', 'composition_menage_acte_naissance'],
    ['tutorship_act', 'acte_tutelle'],
    ['household_composition_or_marriage_certificate', 'composition_menage_acte_mariage'],
    ['legal_cohabitation_certificate', 'attestation_cohabitation_legale'],
    ['parent_identity_card', 'carte_identite_parent'],
    ['parent_long_term_residence_permit', 'titre_sejour_longue_duree_parent'],
    [
        'parent_refugees_stateless_annex_25_26_or_protection_decision',
        'annexe_25_26_refugies_apatrides_decision_protection_parent',
    ],
    ['parent_3_month_residence_permit', 'titre_sejour_3_mois_parent'],
    ['parent_salary_slips', 'fiches_remuneration_parent'],
    ['parent_cpas_certificate', 'attestation_cpas_parent'],
    ['cfwb_scholarship_decision', 'decision_bourse_cfwb'],
    ['scholarship_certificate', 'attestation_boursier'],
    ['ue_long_term_stay_identity_document', 'titre_identite_sejour_longue_duree_ue'],
    ['belgium_residence_permit', 'titre_sejour_belgique'],
    ['stateless_person_proof', 'preuve_statut_apatride'],
    ['a_card', 'carte_a'],
]

general_file_fields = doctorate_file_fields + [
    ['staff_child_certificate', 'attestation_enfant_personnel'],
]


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateAccountingAPIViewTestCase(APITestCase):
    file_uuid = uuid.uuid4()

    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()
        other_promoter = PromoterFactory()

        cls.ca_member = CaMemberFactory(process=promoter.process).person.user
        cls.other_ca_member = CaMemberFactory().person.user

        # Create doctorate management entity
        root = EntityVersionFactory(parent=None).entity
        sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        commission = EntityVersionFactory(
            parent=sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=commission,
            candidate=PersonFactory(country_of_citizenship=None),
            supervision_group=promoter.process,
        )
        other_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
            training__management_entity=commission,
            supervision_group=other_promoter.process,
        )

        # Users
        cls.student = cls.admission.candidate
        cls.other_student = other_admission.candidate
        cls.promoter = promoter.person.user
        cls.other_promoter = other_promoter.person.user

        cls.admission_url = resolve_url('admission_api_v1:doctorate_accounting', uuid=cls.admission.uuid)
        cls.other_admission_url = resolve_url('admission_api_v1:doctorate_accounting', uuid=other_admission.uuid)

        # Data
        cls.be_country = CountryFactory(iso_code='BE')

        cls.doctorate_original_file_uuids = {}
        cls.doctorate_dto_file_uuids = {}
        cls.doctorate_new_file_uuids = {}

        for field in doctorate_file_fields:
            original_uuid = uuid.uuid4()
            cls.doctorate_original_file_uuids[field[0]] = [original_uuid]
            cls.doctorate_dto_file_uuids[field[1]] = [str(original_uuid)]
            cls.doctorate_new_file_uuids[field[1]] = [str(uuid.uuid4())]

        cls.default_api_data = {
            'uuid_proposition': cls.admission.uuid,
            'etudiant_solidaire': False,
            'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            'numero_compte_iban': 'GB87BARC20658244971655',
            'iban_valide': False,
            'prenom_titulaire_compte': 'Jim',
            'nom_titulaire_compte': 'Foe',
            'numero_compte_autre_format': '0203040506',
            'code_bic_swift_banque': 'GKCCBEBA',
            'type_situation_assimilation': TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name,
            'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE.name,
            'sous_type_situation_assimilation_2': ChoixAssimilation2.DEMANDEUR_ASILE.name,
            'sous_type_situation_assimilation_3': ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name,
            'relation_parente': LienParente.COHABITANT_LEGAL.name,
            'sous_type_situation_assimilation_5': ChoixAssimilation5.A_NATIONALITE_UE.name,
            'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE.name,
            **cls.doctorate_new_file_uuids,
        }

    def setUp(self):
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile"})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.confirm_remote_upload", side_effect=lambda token, upload_to: token)
        patcher.start()
        self.addCleanup(patcher.stop)

        # Reset student
        self.student.country_of_citizenship = None
        self.student.save()

        # Reset accounting
        Accounting.objects.filter(admission_id=self.admission.pk).delete()
        AccountingFactory(
            admission_id=self.admission.pk,
            solidarity_student=True,
            account_number_type=ChoixTypeCompteBancaire.IBAN.name,
            iban_account_number='BE43068999999501',
            valid_iban=True,
            other_format_account_number='123456789',
            bic_swift_code='GKCCBEBB',
            account_holder_first_name='John',
            account_holder_last_name='Doe',
            assimilation_situation=TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
            assimilation_1_situation_type=ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
            assimilation_2_situation_type=ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
            assimilation_3_situation_type=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name,
            relationship=LienParente.MERE.name,
            assimilation_5_situation_type=ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name,
            assimilation_6_situation_type=ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
            **self.doctorate_original_file_uuids,
        )

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        not_allowed_methods = [
            'delete',
            'patch',
            'post',
        ]

        for method in not_allowed_methods:
            response = getattr(self.client, method)(self.admission_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_forbidden_request_with_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        forbidden_methods = [
            'get',
            'put',
        ]

        for method in forbidden_methods:
            response = getattr(self.client, method)(self.admission_url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_with_submitted_admission_is_forbidden(self):
        self.client.force_authenticate(user=self.other_student.user)

        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_with_submitted_admission_is_forbidden(self):
        self.client.force_authenticate(user=self.other_student.user)

        response = self.client.put(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_accounting_with_invited_promoter_is_possible(self):
        self.client.force_authenticate(user=self.promoter)

        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_get_accounting_with_not_invited_promoter_is_not_possible(self):
        self.client.force_authenticate(user=self.other_promoter)

        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_get_accounting_with_invited_member_is_possible(self):
        self.client.force_authenticate(user=self.ca_member)

        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_get_accounting_with_not_invited_member_is_not_possible(self):
        self.client.force_authenticate(user=self.other_ca_member)

        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_get_accounting_with_student_without_any_academic_experience(self):
        self.client.force_authenticate(user=self.student.user)
        assimilation_5_choice = (
            ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name
        )

        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                'a_nationalite_ue': None,
                'derniers_etablissements_superieurs_communaute_fr_frequentes': None,
                'etudiant_solidaire': True,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
                'iban_valide': True,
                'numero_compte_autre_format': '123456789',
                'code_bic_swift_banque': 'GKCCBEBB',
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
                'type_situation_assimilation': TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
                'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
                'sous_type_situation_assimilation_3': (
                    ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name
                ),
                'relation_parente': LienParente.MERE.name,
                'sous_type_situation_assimilation_5': assimilation_5_choice,
                'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
                **self.doctorate_dto_file_uuids,
            },
        )

    def test_get_accounting_with_student_with_educational_experiences(self):
        self.client.force_authenticate(user=self.student.user)
        # The candidate attends some high education institute
        current_year = get_current_year()
        experiences = [
            # French community institute -> must be returned
            EducationalExperienceFactory(
                person=self.student,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.FRENCH_SPEAKING.name,
                    acronym='INSTITUTE',
                    name='First institute',
                ),
            ),
            # UCL Louvain -> must be excluded
            EducationalExperienceFactory(
                person=self.student,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.FRENCH_SPEAKING.name,
                    acronym=UCLouvain_acronym,
                    name='Second institute',
                ),
            ),
            # French community institute -> must be returned
            EducationalExperienceFactory(
                person=self.student,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.FRENCH_SPEAKING.name,
                    acronym='INSTITUTE',
                    name='Third institute',
                ),
            ),
            # German community institute -> must be excluded
            EducationalExperienceFactory(
                person=self.student,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.GERMAN_SPEAKING.name,
                    acronym='INSTITUTE',
                    name='Fourth institute',
                ),
            ),
        ]
        for experience in experiences:
            EducationalExperienceYearFactory(
                educational_experience=experience,
                academic_year=AcademicYearFactory(year=current_year),
            )

        # French community institute but out of the range of require years -> must be excluded
        experience = EducationalExperienceFactory(
            person=self.student,
            obtained_diploma=False,
            country=self.be_country,
            institute=OrganizationFactory(
                community=CommunityEnum.FRENCH_SPEAKING.name,
                acronym='INSTITUTE',
                name='Fifth institute',
            ),
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=AcademicYearFactory(year=2000),
        )

        response = self.client.get(self.admission_url)
        last_institutes_attended = response.json().get('derniers_etablissements_superieurs_communaute_fr_frequentes')
        self.assertIsNotNone(last_institutes_attended)
        self.assertEqual(last_institutes_attended.get('academic_year'), current_year)
        self.assertCountEqual(last_institutes_attended.get('names'), ['First institute', 'Third institute'])

    def test_put_accounting_values_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        response = self.client.put(self.admission_url, data=self.default_api_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check updated data
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_200_OK)

        expected_response_data = self.default_api_data.copy()
        expected_response_data.pop('uuid_proposition')
        expected_response_data['derniers_etablissements_superieurs_communaute_fr_frequentes'] = None
        expected_response_data['a_nationalite_ue'] = None

        self.assertEqual(response.json(), expected_response_data)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class GeneralAccountingAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = GeneralEducationAdmissionFactory(
            candidate=PersonFactory(country_of_citizenship=None),
        )

        other_admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
        )

        # Users
        cls.student = cls.admission.candidate
        cls.other_student = other_admission.candidate

        cls.admission_url = resolve_url('admission_api_v1:general_accounting', uuid=cls.admission.uuid)
        cls.other_admission_url = resolve_url('admission_api_v1:general_accounting', uuid=other_admission.uuid)

        # Data
        cls.be_country = CountryFactory(iso_code='BE')

        cls.general_original_file_uuids = {}
        cls.general_dto_file_uuids = {}
        cls.general_new_file_uuids = {}

        for field in general_file_fields:
            original_uuid = uuid.uuid4()
            cls.general_original_file_uuids[field[0]] = [original_uuid]
            cls.general_dto_file_uuids[field[1]] = [str(original_uuid)]
            cls.general_new_file_uuids[field[1]] = [str(uuid.uuid4())]

        cls.default_api_data = {
            'uuid_proposition': cls.admission.uuid,
            'demande_allocation_d_etudes_communaute_francaise_belgique': True,
            'enfant_personnel': True,
            'type_situation_assimilation': TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name,
            'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE.name,
            'sous_type_situation_assimilation_2': ChoixAssimilation2.DEMANDEUR_ASILE.name,
            'sous_type_situation_assimilation_3': ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name,
            'relation_parente': LienParente.COHABITANT_LEGAL.name,
            'sous_type_situation_assimilation_5': ChoixAssimilation5.A_NATIONALITE_UE.name,
            'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE.name,
            'affiliation_sport': ChoixAffiliationSport.TOURNAI_UCL.name,
            'etudiant_solidaire': True,
            'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            'numero_compte_iban': 'GB87BARC20658244971655',
            'iban_valide': True,
            'prenom_titulaire_compte': 'John',
            'nom_titulaire_compte': 'Doe',
            'numero_compte_autre_format': '0203040506',
            'code_bic_swift_banque': 'GKCCBEBB',
            **cls.general_new_file_uuids,
        }

    def setUp(self):
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile"})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.confirm_remote_upload", side_effect=lambda token, upload_to: token)
        patcher.start()
        self.addCleanup(patcher.stop)

        # Reset student
        self.student.country_of_citizenship = None
        self.student.save()

        # Reset accounting
        Accounting.objects.filter(admission_id=self.admission.pk).delete()
        AccountingFactory(
            admission_id=self.admission.pk,
            french_community_study_allowance_application=False,
            is_staff_child=False,
            assimilation_situation=TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
            assimilation_1_situation_type=ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
            assimilation_2_situation_type=ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
            assimilation_3_situation_type=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name,
            relationship=LienParente.MERE.name,
            assimilation_5_situation_type=ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name,
            assimilation_6_situation_type=ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
            sport_affiliation=ChoixAffiliationSport.LOUVAIN_WOLUWE.name,
            solidarity_student=False,
            account_number_type=ChoixTypeCompteBancaire.IBAN.name,
            iban_account_number='BE43068999999501',
            valid_iban=False,
            other_format_account_number='123456789',
            bic_swift_code='GKCCBEBB',
            account_holder_first_name='John',
            account_holder_last_name='Doe',
            **self.general_original_file_uuids,
        )

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        not_allowed_methods = [
            'delete',
            'patch',
            'post',
        ]

        for method in not_allowed_methods:
            response = getattr(self.client, method)(self.admission_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_forbidden_request_with_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        forbidden_methods = [
            'get',
            'put',
        ]

        for method in forbidden_methods:
            response = getattr(self.client, method)(self.admission_url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_with_submitted_admission_is_forbidden(self):
        self.client.force_authenticate(user=self.other_student.user)

        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_with_submitted_admission_is_forbidden(self):
        self.client.force_authenticate(user=self.other_student.user)

        response = self.client.put(self.admission_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_accounting_with_student_without_any_academic_experience(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        assimilation_5_choice = (
            ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name
        )
        self.assertEqual(
            response.json(),
            {
                'a_nationalite_ue': None,
                'derniers_etablissements_superieurs_communaute_fr_frequentes': None,
                'demande_allocation_d_etudes_communaute_francaise_belgique': False,
                'enfant_personnel': False,
                'type_situation_assimilation': TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
                'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
                'sous_type_situation_assimilation_3': (
                    ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name
                ),
                'relation_parente': LienParente.MERE.name,
                'sous_type_situation_assimilation_5': assimilation_5_choice,
                'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
                'affiliation_sport': ChoixAffiliationSport.LOUVAIN_WOLUWE.name,
                'etudiant_solidaire': False,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
                'iban_valide': False,
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
                'numero_compte_autre_format': '123456789',
                'code_bic_swift_banque': 'GKCCBEBB',
                **self.general_dto_file_uuids,
            },
        )

    def test_get_accounting_with_student_with_educational_experiences(self):
        self.client.force_authenticate(user=self.student.user)
        # The candidate attends some high education institute
        current_year = get_current_year()
        experiences = [
            # French community institute -> must be returned
            EducationalExperienceFactory(
                person=self.student,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.FRENCH_SPEAKING.name,
                    acronym='INSTITUTE',
                    name='First institute',
                ),
            ),
            # UCL Louvain -> must be excluded
            EducationalExperienceFactory(
                person=self.student,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.FRENCH_SPEAKING.name,
                    acronym=UCLouvain_acronym,
                    name='Second institute',
                ),
            ),
            # French community institute -> must be returned
            EducationalExperienceFactory(
                person=self.student,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.FRENCH_SPEAKING.name,
                    acronym='INSTITUTE',
                    name='Third institute',
                ),
            ),
            # German community institute -> must be excluded
            EducationalExperienceFactory(
                person=self.student,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.GERMAN_SPEAKING.name,
                    acronym='INSTITUTE',
                    name='Fourth institute',
                ),
            ),
        ]
        for experience in experiences:
            EducationalExperienceYearFactory(
                educational_experience=experience,
                academic_year=AcademicYearFactory(year=current_year),
            )

        # French community institute but out of the range of require years -> must be excluded
        experience = EducationalExperienceFactory(
            person=self.student,
            obtained_diploma=False,
            country=self.be_country,
            institute=OrganizationFactory(
                community=CommunityEnum.FRENCH_SPEAKING.name,
                acronym='INSTITUTE',
                name='Fifth institute',
            ),
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=AcademicYearFactory(year=2000),
        )

        response = self.client.get(self.admission_url)
        last_institutes_attended = response.json().get('derniers_etablissements_superieurs_communaute_fr_frequentes')
        self.assertIsNotNone(last_institutes_attended)
        self.assertEqual(last_institutes_attended.get('academic_year'), current_year)
        self.assertCountEqual(last_institutes_attended.get('names'), ['First institute', 'Third institute'])

    def test_get_accounting_with_student_with_ue_nationality(self):
        self.client.force_authenticate(user=self.student.user)
        self.student.country_of_citizenship = CountryFactory(european_union=True)
        self.student.save()
        response = self.client.get(self.admission_url)
        self.assertTrue(response.json().get('a_nationalite_ue'))

    def test_get_accounting_with_student_with_not_ue_nationality(self):
        self.client.force_authenticate(user=self.student.user)
        self.student.country_of_citizenship = CountryFactory(european_union=False)
        self.student.save()
        response = self.client.get(self.admission_url)
        self.assertFalse(response.json().get('a_nationalite_ue'))

    def test_put_accounting_values_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        response = self.client.put(self.admission_url, data=self.default_api_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check updated data
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_200_OK)

        expected_response_data = self.default_api_data.copy()
        expected_response_data.pop('uuid_proposition')
        expected_response_data['derniers_etablissements_superieurs_communaute_fr_frequentes'] = None
        expected_response_data['a_nationalite_ue'] = None

        self.assertEqual(response.json(), expected_response_data)
