# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import uuid
from unittest.mock import patch

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from admission.contrib.models import Accounting
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixAffiliationSport,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixStatutProposition,
    ChoixTypeCompteBancaire,
    LienParente,
    TypeSituationAssimilation,
)

from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CddManagerFactory
from admission.tests.factories.supervision import PromoterFactory
from base.models.enums.community import CommunityEnum
from base.models.enums.entity_type import EntityType
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from osis_profile.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from reference.tests.factories.country import CountryFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class AccountingAPIViewTestCase(APITestCase):
    file_uuid = uuid.uuid4()

    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()
        other_promoter = PromoterFactory()

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
        )
        other_admission = DoctorateAdmissionFactory(
            status=ChoixStatutProposition.ENROLLED.name,
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
            training__management_entity=commission,
            supervision_group=other_promoter.process,
        )

        # Users
        cls.student = cls.admission.candidate
        cls.other_student = other_admission.candidate
        cls.promoter = promoter.person.user
        cls.other_promoter = other_promoter.person.user
        cls.cdd_person = CddManagerFactory(entity=commission).person

        cls.admission_url = resolve_url('admission_api_v1:accounting', uuid=cls.admission.uuid)
        cls.other_admission_url = resolve_url('admission_api_v1:accounting', uuid=other_admission.uuid)

        # Data
        cls.be_country = CountryFactory(iso_code='BE')

        cls.file_uuids = {
            field: uuid.uuid4()
            for field in [
                'attestation_absence_dette_etablissement',
                'attestation_enfant_personnel',
                'carte_resident_longue_duree',
                'carte_cire_sejour_illimite_etranger',
                'carte_sejour_membre_ue',
                'carte_sejour_permanent_membre_ue',
                'carte_a_b_refugie',
                'annexe_25_26_refugies_apatrides',
                'attestation_immatriculation',
                'carte_a_b',
                'decision_protection_subsidiaire',
                'decision_protection_temporaire',
                'titre_sejour_3_mois_professionel',
                'fiches_remuneration',
                'titre_sejour_3_mois_remplacement',
                'preuve_allocations_chomage_pension_indemnite',
                'attestation_cpas',
                'composition_menage_acte_naissance',
                'acte_tutelle',
                'composition_menage_acte_mariage',
                'attestation_cohabitation_legale',
                'carte_identite_parent',
                'titre_sejour_longue_duree_parent',
                'annexe_25_26_refugies_apatrides_decision_protection_parent',
                'titre_sejour_3_mois_parent',
                'fiches_remuneration_parent',
                'attestation_cpas_parent',
                'decision_bourse_cfwb',
                'attestation_boursier',
                'titre_identite_sejour_longue_duree_ue',
                'titre_sejour_belgique',
            ]
        }

        cls.default_api_data = {
            'uuid_proposition': cls.admission.uuid,
            'attestation_absence_dette_etablissement': [str(cls.file_uuids['attestation_absence_dette_etablissement'])],
            'demande_allocation_d_etudes_communaute_francaise_belgique': True,
            'enfant_personnel': True,
            'attestation_enfant_personnel': [str(cls.file_uuids['attestation_enfant_personnel'])],
            'type_situation_assimilation': TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name,
            'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE.name,
            'carte_resident_longue_duree': [str(cls.file_uuids['carte_resident_longue_duree'])],
            'carte_cire_sejour_illimite_etranger': [str(cls.file_uuids['carte_cire_sejour_illimite_etranger'])],
            'carte_sejour_membre_ue': [str(cls.file_uuids['carte_sejour_membre_ue'])],
            'carte_sejour_permanent_membre_ue': [str(cls.file_uuids['carte_sejour_permanent_membre_ue'])],
            'sous_type_situation_assimilation_2': ChoixAssimilation2.DEMANDEUR_ASILE.name,
            'carte_a_b_refugie': [str(cls.file_uuids['carte_a_b_refugie'])],
            'annexe_25_26_refugies_apatrides': [str(cls.file_uuids['annexe_25_26_refugies_apatrides'])],
            'attestation_immatriculation': [str(cls.file_uuids['attestation_immatriculation'])],
            'carte_a_b': [str(cls.file_uuids['carte_a_b'])],
            'decision_protection_subsidiaire': [str(cls.file_uuids['decision_protection_subsidiaire'])],
            'decision_protection_temporaire': [str(cls.file_uuids['decision_protection_temporaire'])],
            'sous_type_situation_assimilation_3': ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name,
            'titre_sejour_3_mois_professionel': [str(cls.file_uuids['titre_sejour_3_mois_professionel'])],
            'fiches_remuneration': [str(cls.file_uuids['fiches_remuneration'])],
            'titre_sejour_3_mois_remplacement': [str(cls.file_uuids['titre_sejour_3_mois_remplacement'])],
            'preuve_allocations_chomage_pension_indemnite': [
                str(cls.file_uuids['preuve_allocations_chomage_pension_indemnite'])
            ],
            'attestation_cpas': [str(cls.file_uuids['attestation_cpas'])],
            'relation_parente': LienParente.COHABITANT_LEGAL.name,
            'composition_menage_acte_naissance': [str(cls.file_uuids['composition_menage_acte_naissance'])],
            'acte_tutelle': [str(cls.file_uuids['acte_tutelle'])],
            'composition_menage_acte_mariage': [str(cls.file_uuids['composition_menage_acte_mariage'])],
            'attestation_cohabitation_legale': [str(cls.file_uuids['attestation_cohabitation_legale'])],
            'sous_type_situation_assimilation_5': ChoixAssimilation5.A_NATIONALITE_UE.name,
            'carte_identite_parent': [str(cls.file_uuids['carte_identite_parent'])],
            'titre_sejour_longue_duree_parent': [str(cls.file_uuids['titre_sejour_longue_duree_parent'])],
            'annexe_25_26_refugies_apatrides_decision_protection_parent': [
                str(cls.file_uuids['annexe_25_26_refugies_apatrides_decision_protection_parent'])
            ],
            'titre_sejour_3_mois_parent': [str(cls.file_uuids['titre_sejour_3_mois_parent'])],
            'fiches_remuneration_parent': [str(cls.file_uuids['fiches_remuneration_parent'])],
            'attestation_cpas_parent': [str(cls.file_uuids['attestation_cpas_parent'])],
            'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE.name,
            'decision_bourse_cfwb': [str(cls.file_uuids['decision_bourse_cfwb'])],
            'attestation_boursier': [str(cls.file_uuids['attestation_boursier'])],
            'titre_identite_sejour_longue_duree_ue': [str(cls.file_uuids['titre_identite_sejour_longue_duree_ue'])],
            'titre_sejour_belgique': [str(cls.file_uuids['titre_sejour_belgique'])],
            'affiliation_sport': ChoixAffiliationSport.TOURNAI_UCL.name,
            'etudiant_solidaire': True,
            'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
            'numero_compte_iban': 'GB87BARC20658244971655',
            'iban_valide': True,
            'prenom_titulaire_compte': 'John',
            'nom_titulaire_compte': 'Doe',
            'numero_compte_autre_format': '0203040506',
            'code_bic_swift_banque': 'GKCCBEBB',
        }

    def setUp(self):
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile"})
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, upload_to: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.student.country_of_citizenship = None
        self.student.save()
        Accounting.objects.filter(admission_id=self.admission.pk).delete()

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

    def test_get_accounting_conditions_with_student_with_no_values(self):
        self.client.force_authenticate(user=self.student.user)

        # The candidate doesn't specify a country of citizenship or any academic experiences
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                'has_ue_nationality': None,
                'last_french_community_high_education_institutes_attended': None,
            },
        )

    def test_get_accounting_conditions_with_country_of_citizenship_outside_ue(self):
        # The candidate specifies a country of citizenship -> not UE
        self.client.force_authenticate(user=self.student.user)
        self.student.country_of_citizenship = CountryFactory(european_union=False)
        self.student.save()
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json().get('has_ue_nationality'), False)

    def test_get_accounting_conditions_with_country_of_citizenship_inside_ue(self):
        # The candidate specifies a country of citizenship -> UE
        self.client.force_authenticate(user=self.student.user)
        self.student.country_of_citizenship = CountryFactory(european_union=True)
        self.student.save()
        response = self.client.get(self.admission_url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json().get('has_ue_nationality'), True)

    def test_get_accounting_conditions_with_specified_educational_experiences(self):
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
                    code='INSTITUTE',
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
                    code=UCLouvain_acronym,
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
                    code='INSTITUTE',
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
                    code='INSTITUTE',
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
                code='INSTITUTE',
                name='Fourth institute',
            ),
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=AcademicYearFactory(year=2000),
        )

        response = self.client.get(self.admission_url)
        last_institutes_attended = response.json().get('last_french_community_high_education_institutes_attended')
        self.assertIsNotNone(last_institutes_attended)
        self.assertEqual(last_institutes_attended.get('academic_year'), current_year)
        self.assertCountEqual(last_institutes_attended.get('names'), ['First institute', 'Third institute'])

    def test_forbidden_request_with_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        forbidden_methods = [
            'get',
            'put',
        ]

        for method in forbidden_methods:
            response = getattr(self.client, method)(self.admission_url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_accounting_values_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        response = self.client.put(
            self.admission_url,
            data=self.default_api_data,
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check updated data
        accounting = Accounting.objects.get(admission_id=self.admission.pk)

        self.assertEqual(
            accounting.institute_absence_debts_certificate,
            [self.file_uuids['attestation_absence_dette_etablissement']],
        )

        self.assertEqual(
            accounting.french_community_study_allowance_application,
            True,
        )
        self.assertEqual(
            accounting.is_staff_child,
            True,
        )
        self.assertEqual(
            accounting.staff_child_certificate,
            [self.file_uuids['attestation_enfant_personnel']],
        )

        self.assertEqual(
            accounting.assimilation_situation,
            TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name,
        )

        self.assertEqual(
            accounting.assimilation_1_situation_type,
            ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE.name,
        )
        self.assertEqual(
            accounting.long_term_resident_card,
            [self.file_uuids['carte_resident_longue_duree']],
        )
        self.assertEqual(
            accounting.cire_unlimited_stay_foreigner_card,
            [self.file_uuids['carte_cire_sejour_illimite_etranger']],
        )
        self.assertEqual(
            accounting.ue_family_member_residence_card,
            [self.file_uuids['carte_sejour_membre_ue']],
        )
        self.assertEqual(
            accounting.ue_family_member_permanent_residence_card,
            [self.file_uuids['carte_sejour_permanent_membre_ue']],
        )

        self.assertEqual(
            accounting.assimilation_2_situation_type,
            ChoixAssimilation2.DEMANDEUR_ASILE.name,
        )
        self.assertEqual(
            accounting.refugee_a_b_card,
            [self.file_uuids['carte_a_b_refugie']],
        )
        self.assertEqual(
            accounting.refugees_stateless_annex_25_26,
            [self.file_uuids['annexe_25_26_refugies_apatrides']],
        )
        self.assertEqual(
            accounting.registration_certificate,
            [self.file_uuids['attestation_immatriculation']],
        )
        self.assertEqual(
            accounting.a_b_card,
            [self.file_uuids['carte_a_b']],
        )
        self.assertEqual(
            accounting.subsidiary_protection_decision,
            [self.file_uuids['decision_protection_subsidiaire']],
        )
        self.assertEqual(
            accounting.temporary_protection_decision,
            [self.file_uuids['decision_protection_temporaire']],
        )

        self.assertEqual(
            accounting.assimilation_3_situation_type,
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name,
        )
        self.assertEqual(
            accounting.professional_3_month_residence_permit,
            [self.file_uuids['titre_sejour_3_mois_professionel']],
        )
        self.assertEqual(
            accounting.salary_slips,
            [self.file_uuids['fiches_remuneration']],
        )
        self.assertEqual(
            accounting.replacement_3_month_residence_permit,
            [self.file_uuids['titre_sejour_3_mois_remplacement']],
        )
        self.assertEqual(
            accounting.unemployment_benefit_pension_compensation_proof,
            [self.file_uuids['preuve_allocations_chomage_pension_indemnite']],
        )

        self.assertEqual(
            accounting.cpas_certificate,
            [self.file_uuids['attestation_cpas']],
        )

        self.assertEqual(
            accounting.relationship,
            LienParente.COHABITANT_LEGAL.name,
        )
        self.assertEqual(
            accounting.household_composition_or_birth_certificate,
            [self.file_uuids['composition_menage_acte_naissance']],
        )
        self.assertEqual(
            accounting.tutorship_act,
            [self.file_uuids['acte_tutelle']],
        )
        self.assertEqual(
            accounting.household_composition_or_marriage_certificate,
            [self.file_uuids['composition_menage_acte_mariage']],
        )
        self.assertEqual(
            accounting.legal_cohabitation_certificate,
            [self.file_uuids['attestation_cohabitation_legale']],
        )
        self.assertEqual(
            accounting.assimilation_5_situation_type,
            ChoixAssimilation5.A_NATIONALITE_UE.name,
        )
        self.assertEqual(
            accounting.parent_identity_card,
            [self.file_uuids['carte_identite_parent']],
        )
        self.assertEqual(
            accounting.parent_long_term_residence_permit,
            [self.file_uuids['titre_sejour_longue_duree_parent']],
        )
        self.assertEqual(
            accounting.parent_refugees_stateless_annex_25_26_or_protection_decision,
            [self.file_uuids['annexe_25_26_refugies_apatrides_decision_protection_parent']],
        )
        self.assertEqual(
            accounting.parent_3_month_residence_permit,
            [self.file_uuids['titre_sejour_3_mois_parent']],
        )
        self.assertEqual(
            accounting.parent_salary_slips,
            [self.file_uuids['fiches_remuneration_parent']],
        )
        self.assertEqual(
            accounting.parent_cpas_certificate,
            [self.file_uuids['attestation_cpas_parent']],
        )

        self.assertEqual(
            accounting.assimilation_6_situation_type,
            ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE.name,
        )
        self.assertEqual(
            accounting.cfwb_scholarship_decision,
            [self.file_uuids['decision_bourse_cfwb']],
        )
        self.assertEqual(
            accounting.scholarship_certificate,
            [self.file_uuids['attestation_boursier']],
        )

        self.assertEqual(
            accounting.ue_long_term_stay_identity_document,
            [self.file_uuids['titre_identite_sejour_longue_duree_ue']],
        )
        self.assertEqual(
            accounting.belgium_residence_permit,
            [self.file_uuids['titre_sejour_belgique']],
        )

        self.assertEqual(
            accounting.sport_affiliation,
            ChoixAffiliationSport.TOURNAI_UCL.name,
        )
        self.assertEqual(
            accounting.solidarity_student,
            True,
        )

        self.assertEqual(
            accounting.account_number_type,
            ChoixTypeCompteBancaire.IBAN.name,
        )
        self.assertEqual(
            accounting.iban_account_number,
            'GB87BARC20658244971655',
        )
        self.assertEqual(
            accounting.account_holder_first_name,
            'John',
        )
        self.assertEqual(
            accounting.account_holder_last_name,
            'Doe',
        )
        self.assertEqual(
            accounting.other_format_account_number,
            '0203040506',
        )
        self.assertEqual(
            accounting.bic_swift_code,
            'GKCCBEBB',
        )

        # Check output data
        response = self.client.get(
            resolve_url('admission_api_v1:propositions', uuid=self.admission.uuid),
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        dto_accounting = self.default_api_data.copy()
        dto_accounting.pop('uuid_proposition', None)

        self.assertEqual(response.json().get('comptabilite'), dto_accounting)

    def test_get_proposition_with_empty_accounting(self):
        self.client.force_authenticate(user=self.student.user)

        # Check output data
        response = self.client.get(
            resolve_url('admission_api_v1:propositions', uuid=self.admission.uuid),
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            response.json().get('comptabilite'),
            {
                'attestation_absence_dette_etablissement': [],
                'demande_allocation_d_etudes_communaute_francaise_belgique': None,
                'enfant_personnel': None,
                'attestation_enfant_personnel': [],
                'type_situation_assimilation': '',
                'sous_type_situation_assimilation_1': '',
                'carte_resident_longue_duree': [],
                'carte_cire_sejour_illimite_etranger': [],
                'carte_sejour_membre_ue': [],
                'carte_sejour_permanent_membre_ue': [],
                'sous_type_situation_assimilation_2': '',
                'carte_a_b_refugie': [],
                'annexe_25_26_refugies_apatrides': [],
                'attestation_immatriculation': [],
                'carte_a_b': [],
                'decision_protection_subsidiaire': [],
                'decision_protection_temporaire': [],
                'sous_type_situation_assimilation_3': '',
                'titre_sejour_3_mois_professionel': [],
                'fiches_remuneration': [],
                'titre_sejour_3_mois_remplacement': [],
                'preuve_allocations_chomage_pension_indemnite': [],
                'attestation_cpas': [],
                'relation_parente': '',
                'sous_type_situation_assimilation_5': '',
                'composition_menage_acte_naissance': [],
                'acte_tutelle': [],
                'composition_menage_acte_mariage': [],
                'attestation_cohabitation_legale': [],
                'carte_identite_parent': [],
                'titre_sejour_longue_duree_parent': [],
                'annexe_25_26_refugies_apatrides_decision_protection_parent': [],
                'titre_sejour_3_mois_parent': [],
                'fiches_remuneration_parent': [],
                'attestation_cpas_parent': [],
                'sous_type_situation_assimilation_6': '',
                'decision_bourse_cfwb': [],
                'attestation_boursier': [],
                'titre_identite_sejour_longue_duree_ue': [],
                'titre_sejour_belgique': [],
                'affiliation_sport': '',
                'etudiant_solidaire': None,
                'type_numero_compte': '',
                'numero_compte_iban': '',
                'iban_valide': None,
                'numero_compte_autre_format': '',
                'code_bic_swift_banque': '',
                'prenom_titulaire_compte': '',
                'nom_titulaire_compte': '',
            },
        )
