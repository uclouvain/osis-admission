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
from decimal import Decimal
from unittest.mock import ANY, patch

import freezegun
from django.test import TestCase, override_settings
from django.utils.translation import pgettext
from osis_history.models import HistoryEntry

from admission.contrib.models import DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.commands import RecupererPropositionGestionnaireQuery
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    TypeDeRefus,
    BesoinDeDerogation,
    DroitsInscriptionMontant,
    DispenseOuDroitsMajores,
    MobiliteNombreDeMois,
    DerogationFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratDTO
from admission.ddd.admission.doctorat.preparation.dtos.condition_approbation import (
    ConditionComplementaireApprobationDTO,
)
from admission.ddd.admission.doctorat.preparation.dtos.proposition import PropositionGestionnaireDTO
from admission.ddd.admission.domain.model.enums.equivalence import (
    TypeEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    EtatEquivalenceTitreAcces,
)
from admission.ddd.admission.dtos.bourse import BourseDTO
from admission.ddd.admission.dtos.formation import BaseFormationDTO
from admission.ddd.admission.formation_generale.domain.model.enums import DROITS_INSCRIPTION_MONTANT_VALEURS
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.faculty_decision import (
    RefusalReasonFactory,
    AdditionalApprovalConditionFactory,
    FreeAdditionalApprovalConditionFactory,
    DoctorateFreeAdditionalApprovalConditionFactory,
)
from admission.tests.factories.scholarship import DoctorateScholarshipFactory
from base.models.enums.organization_type import MAIN
from base.models.person import Person
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.financabilite.domain.model.enums.situation import SituationFinancabilite
from epc.models.enums.condition_acces import ConditionAcces
from infrastructure.messages_bus import message_bus_instance
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from program_management.models.education_group_version import EducationGroupVersion
from reference.tests.factories.country import CountryFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
@freezegun.freeze_time('2023-01-01')
class GetPropositionDTOForGestionnaireTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.country = CountryFactory()
        cls.france_country = CountryFactory(iso_code='FR')
        cls.files_uuids = {
            name_field: [uuid.uuid4()]
            for name_field in [
                'fac_refusal_certificate',
                'fac_approval_certificate',
                'sic_approval_certificate',
                'sic_annexe_approval_certificate',
                'sic_refusal_certificate',
                'must_provide_student_visa_d',
                'student_visa_d',
                'signed_enrollment_authorization',
            ]
        }

    def setUp(self) -> None:
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        school = EntityFactory()
        EntityVersionFactory(entity=school, acronym='SCH', parent=first_doctoral_commission)

        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            training__management_entity=school,
            international_scholarship=None,
            candidate__private_email='john.doe@example.com',
            candidate__country_of_citizenship=self.country,
            refusal_type=TypeDeRefus.REFUS_LIBRE.name,
            dispensation_needed=BesoinDeDerogation.BESOIN_DE_COMPLEMENT.name,
            tuition_fees_amount=DroitsInscriptionMontant.DROITS_MAJORES.name,
            tuition_fees_amount_other=Decimal(10),
            tuition_fees_dispensation=DispenseOuDroitsMajores.DROITS_MAJORES_DEMANDES.name,
            particular_cost='10.2',
            rebilling_or_third_party_payer='Info',
            first_year_inscription_and_status='2021',
            is_mobility=True,
            mobility_months_amount=MobiliteNombreDeMois.SIX.name,
            must_report_to_sic=True,
            communication_to_the_candidate='Communication',
            admission_requirement=ConditionAcces.EXAMEN_ADMISSION.name,
            admission_requirement_year=AcademicYearFactory(),
            foreign_access_title_equivalency_type=TypeEquivalenceTitreAcces.EQUIVALENCE_DE_NIVEAU.name,
            foreign_access_title_equivalency_status=StatutEquivalenceTitreAcces.COMPLETE.name,
            foreign_access_title_equivalency_restriction_about='About',
            foreign_access_title_equivalency_state=EtatEquivalenceTitreAcces.DEFINITIVE.name,
            foreign_access_title_equivalency_effective_date=datetime.date(2020, 1, 1),
            financability_computed_rule=EtatFinancabilite.FINANCABLE.name,
            financability_computed_rule_situation=SituationFinancabilite.REUSSI_1_UE_BLOC_1.name,
            financability_computed_rule_on=datetime.datetime(2020, 1, 1),
            financability_rule=SituationFinancabilite.PLUS_FINANCABLE.name,
            financability_rule_established_by=PersonFactory(),
            financability_rule_established_on=datetime.datetime(2020, 1, 2),
            financability_dispensation_status=DerogationFinancement.ACCORD_DE_DEROGATION_FACULTAIRE.name,
            financability_dispensation_first_notification_on=datetime.datetime(2020, 1, 3),
            financability_dispensation_first_notification_by=PersonFactory(),
            financability_dispensation_last_notification_on=datetime.datetime(2020, 1, 4),
            financability_dispensation_last_notification_by=PersonFactory(),
            fac_refusal_certificate=self.files_uuids['fac_refusal_certificate'],
            fac_approval_certificate=self.files_uuids['fac_approval_certificate'],
            sic_approval_certificate=self.files_uuids['sic_approval_certificate'],
            sic_annexe_approval_certificate=self.files_uuids['sic_annexe_approval_certificate'],
            sic_refusal_certificate=self.files_uuids['sic_refusal_certificate'],
            must_provide_student_visa_d=True,
            student_visa_d=self.files_uuids['student_visa_d'],
            signed_enrollment_authorization=self.files_uuids['signed_enrollment_authorization'],
        )

        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile", "size": 1})
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.confirm_remote_upload", return_value=str(uuid.uuid4()))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            'osis_document.contrib.fields.FileField._confirm_multiple_upload',
            side_effect=lambda _, value, __: [str(uuid.uuid4())] if value else [],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _get_command_result(self, uuid_proposition=None) -> PropositionGestionnaireDTO:
        return message_bus_instance.invoke(
            RecupererPropositionGestionnaireQuery(uuid_proposition=uuid_proposition or self.admission.uuid),
        )

    def test_get_proposition_with_base_data(self):
        result = self._get_command_result()

        self.assertEqual(result.uuid, self.admission.uuid)
        self.assertEqual(
            result.doctorat,
            DoctoratDTO(
                sigle=self.admission.training.acronym,
                code=self.admission.training.partial_acronym,
                annee=self.admission.training.academic_year.year,
                intitule=self.admission.training.title,
                intitule_fr=self.admission.training.title,
                intitule_en=self.admission.training.title_english,
                campus=ANY,
                type=self.admission.training.education_group_type.name,
                campus_inscription=ANY,
                sigle_entite_gestion='SCH',
                credits=self.admission.training.credits,
                date_debut=self.admission.training.academic_year.start_date,
            ),
        )
        self.assertEqual(result.reference, f'M-SCH22-{self.admission}')
        self.assertEqual(result.creee_le, self.admission.created_at)
        self.assertEqual(result.modifiee_le, self.admission.modified_at)
        self.assertEqual(result.soumise_le, self.admission.submitted_at)
        self.assertEqual(result.statut, self.admission.status)
        self.assertEqual(result.matricule_candidat, self.admission.candidate.global_id)
        self.assertEqual(result.prenom_candidat, self.admission.candidate.first_name)
        self.assertEqual(result.nom_candidat, self.admission.candidate.last_name)
        self.assertEqual(result.curriculum, self.admission.curriculum)
        self.assertEqual(result.pdf_recapitulatif, self.admission.pdf_recap)
        self.assertEqual(result.type_demande, self.admission.type_demande)
        self.assertEqual(result.date_changement_statut, None)
        self.assertEqual(result.genre_candidat, self.admission.candidate.gender)
        self.assertEqual(result.noma_candidat, '')
        self.assertEqual(result.adresse_email_candidat, self.admission.candidate.private_email)
        self.assertEqual(result.langue_contact_candidat, self.admission.candidate.language)
        self.assertEqual(result.nationalite_candidat, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_fr, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_en, self.admission.candidate.country_of_citizenship.name_en)
        self.assertEqual(result.nationalite_ue_candidat, self.admission.candidate.country_of_citizenship.european_union)
        self.assertEqual(result.nationalite_candidat_code_iso, self.admission.candidate.country_of_citizenship.iso_code)
        self.assertEqual(result.photo_identite_candidat, self.admission.candidate.id_card)
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)
        self.assertEqual(result.cotutelle, None)
        self.assertEqual(result.profil_soumis_candidat, None)
        self.assertEqual(result.bourse_recherche, None)
        self.assertEqual(result.type_de_refus, self.admission.refusal_type)
        self.assertEqual(result.besoin_de_derogation, self.admission.dispensation_needed)
        self.assertEqual(result.droits_inscription_montant, self.admission.tuition_fees_amount)
        self.assertEqual(
            result.droits_inscription_montant_valeur,
            DROITS_INSCRIPTION_MONTANT_VALEURS[self.admission.tuition_fees_amount],
        )
        self.assertEqual(result.droits_inscription_montant_autre, self.admission.tuition_fees_amount_other)
        self.assertEqual(result.dispense_ou_droits_majores, self.admission.tuition_fees_dispensation)
        self.assertEqual(result.tarif_particulier, self.admission.particular_cost)
        self.assertEqual(result.refacturation_ou_tiers_payant, self.admission.rebilling_or_third_party_payer)
        self.assertEqual(
            result.annee_de_premiere_inscription_et_statut, self.admission.first_year_inscription_and_status
        )
        self.assertEqual(result.est_mobilite, self.admission.is_mobility)
        self.assertEqual(result.nombre_de_mois_de_mobilite, self.admission.mobility_months_amount)
        self.assertEqual(result.doit_se_presenter_en_sic, self.admission.must_report_to_sic)
        self.assertEqual(result.communication_au_candidat, self.admission.communication_to_the_candidate)
        self.assertEqual(result.condition_acces, self.admission.admission_requirement)
        self.assertEqual(result.millesime_condition_acces, self.admission.admission_requirement_year.year)
        self.assertEqual(result.type_equivalence_titre_acces, self.admission.foreign_access_title_equivalency_type)
        self.assertEqual(result.statut_equivalence_titre_acces, self.admission.foreign_access_title_equivalency_status)
        self.assertEqual(
            result.information_a_propos_de_la_restriction,
            self.admission.foreign_access_title_equivalency_restriction_about,
        )
        self.assertEqual(result.etat_equivalence_titre_acces, self.admission.foreign_access_title_equivalency_state)
        self.assertEqual(
            result.date_prise_effet_equivalence_titre_acces,
            self.admission.foreign_access_title_equivalency_effective_date,
        )
        self.assertEqual(result.financabilite_regle_calcule, self.admission.financability_computed_rule)
        self.assertEqual(
            result.financabilite_regle_calcule_situation,
            self.admission.financability_computed_rule_situation,
        )
        self.assertEqual(result.financabilite_regle_calcule_le, self.admission.financability_computed_rule_on)
        self.assertEqual(result.financabilite_regle, self.admission.financability_rule)
        self.assertEqual(result.financabilite_regle_etabli_par, self.admission.financability_rule_established_by.uuid)
        self.assertEqual(result.financabilite_regle_etabli_le, self.admission.financability_rule_established_on)
        self.assertEqual(result.financabilite_derogation_statut, self.admission.financability_dispensation_status)
        self.assertEqual(
            result.financabilite_derogation_premiere_notification_le,
            self.admission.financability_dispensation_first_notification_on,
        )
        self.assertEqual(
            result.financabilite_derogation_premiere_notification_par,
            self.admission.financability_dispensation_first_notification_by.global_id,
        )
        self.assertEqual(
            result.financabilite_derogation_derniere_notification_le,
            self.admission.financability_dispensation_last_notification_on,
        )
        self.assertEqual(
            result.financabilite_derogation_derniere_notification_par,
            self.admission.financability_dispensation_last_notification_by.global_id,
        )
        self.assertEqual(result.certificat_refus_fac, self.admission.fac_refusal_certificate)
        self.assertEqual(result.certificat_approbation_fac, self.admission.fac_approval_certificate)
        self.assertEqual(result.certificat_approbation_sic, self.admission.sic_approval_certificate)
        self.assertEqual(result.certificat_approbation_sic_annexe, self.admission.sic_annexe_approval_certificate)
        self.assertEqual(result.certificat_refus_sic, self.admission.sic_refusal_certificate)
        self.assertEqual(result.doit_fournir_visa_etudes, self.admission.must_provide_student_visa_d)
        self.assertEqual(result.visa_etudes_d, self.admission.student_visa_d)
        self.assertEqual(result.certificat_autorisation_signe, self.admission.signed_enrollment_authorization)

    def test_get_proposition_with_default_values_if_necessary(self):
        self.admission.tuition_fees_amount = ''
        self.admission.financability_rule_established_by = None
        self.admission.financability_dispensation_first_notification_by = None
        self.admission.financability_dispensation_last_notification_by = None

        self.admission.save()

        result = self._get_command_result()

        self.assertEqual(result.droits_inscription_montant, '')
        self.assertEqual(result.droits_inscription_montant_valeur, None)
        self.assertEqual(result.financabilite_regle_etabli_par, '')
        self.assertEqual(result.financabilite_derogation_premiere_notification_par, '')
        self.assertEqual(result.financabilite_derogation_derniere_notification_par, '')

    def test_get_proposition_with_country_of_citizenship(self):
        self.admission.candidate.country_of_citizenship = CountryFactory()
        self.admission.candidate.save()

        result = self._get_command_result()

        self.assertEqual(result.nationalite_candidat, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_fr, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_en, self.admission.candidate.country_of_citizenship.name_en)
        self.assertEqual(result.nationalite_ue_candidat, self.admission.candidate.country_of_citizenship.european_union)

    def test_get_proposition_with_scholarship(self):
        self.admission.international_scholarship = DoctorateScholarshipFactory()
        self.admission.save()

        result = self._get_command_result()

        self.assertEqual(
            result.bourse_recherche,
            BourseDTO(
                uuid=str(self.admission.international_scholarship.uuid),
                nom_court=self.admission.international_scholarship.short_name,
                nom_long=self.admission.international_scholarship.long_name,
                type=self.admission.international_scholarship.type,
            ),
        )

    def test_get_proposition_with_update_status_history_entry(self):
        self.history_entry = HistoryEntry.objects.create(
            object_uuid=self.admission.uuid,
            tags=['proposition', 'status-changed'],
        )

        result = self._get_command_result()

        self.assertEqual(result.date_changement_statut, self.history_entry.created)

    def test_get_proposition_with_noma(self):
        student = StudentFactory(person=self.admission.candidate)

        result = self._get_command_result()

        self.assertEqual(result.noma_candidat, student.registration_id)

    def test_get_proposition_with_several_enrolments(self):
        second_admission = DoctorateAdmissionFactory(
            candidate=self.admission.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, True)

        second_admission.status = ChoixStatutPropositionDoctorale.ANNULEE.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

        second_admission.status = ChoixStatutPropositionDoctorale.EN_BROUILLON.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

        second_admission.status = ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

    def test_get_unknown_proposition_triggers_exception(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self._get_command_result(uuid_proposition=uuid.uuid4())

    def test_get_proposition_with_cotutelle(self):
        self.admission.cotutelle = True
        self.admission.cotutelle_motivation = 'My motivation'
        self.admission.cotutelle_institution_fwb = True
        self.admission.cotutelle_institution = 'Institute'
        self.admission.cotutelle_opening_request = [uuid.uuid4()]
        self.admission.cotutelle_convention = [uuid.uuid4()]
        self.admission.cotutelle_other_documents = [uuid.uuid4()]

        self.admission.save()

        result = self._get_command_result()

        self.assertIsNotNone(result.cotutelle)

        self.assertEqual(result.cotutelle.cotutelle, True)
        self.assertEqual(result.cotutelle.motivation, 'My motivation')
        self.assertEqual(result.cotutelle.institution_fwb, True)
        self.assertEqual(result.cotutelle.institution, 'Institute')
        self.assertEqual([str(result.cotutelle.demande_ouverture[0])], self.admission.cotutelle_opening_request)
        self.assertEqual([str(result.cotutelle.convention[0])], self.admission.cotutelle_convention)
        self.assertEqual([str(result.cotutelle.autres_documents[0])], self.admission.cotutelle_other_documents)

    def test_get_proposition_with_submitted_profile(self):
        self.admission.submitted_profile = {
            'identification': {
                'last_name': 'Joe',
                'first_name': 'Doe',
                'gender': 'M',
                'country_of_citizenship': 'FR',
                'birth_date': '1990-01-01',
            },
            'coordinates': {
                'country': 'FR',
                'city': 'Paris',
                'street': 'Rue de la Paix',
                'postal_code': '75000',
                'street_number': '1',
                'postal_box': 'A',
            },
        }

        self.admission.save()

        result = self._get_command_result()

        self.assertIsNotNone(result.profil_soumis_candidat)
        self.assertEqual(result.profil_soumis_candidat.nom, 'Joe')
        self.assertEqual(result.profil_soumis_candidat.prenom, 'Doe')
        self.assertEqual(result.profil_soumis_candidat.genre, 'M')
        self.assertEqual(result.profil_soumis_candidat.nationalite, 'FR')
        self.assertEqual(result.profil_soumis_candidat.nom_pays_nationalite, self.france_country.name)
        self.assertEqual(result.profil_soumis_candidat.date_naissance, datetime.date(1990, 1, 1))
        self.assertEqual(result.profil_soumis_candidat.pays, 'FR')
        self.assertEqual(result.profil_soumis_candidat.nom_pays, self.france_country.name)
        self.assertEqual(result.profil_soumis_candidat.code_postal, '75000')
        self.assertEqual(result.profil_soumis_candidat.ville, 'Paris')
        self.assertEqual(result.profil_soumis_candidat.rue, 'Rue de la Paix')
        self.assertEqual(result.profil_soumis_candidat.numero_rue, '1')
        self.assertEqual(result.profil_soumis_candidat.boite_postale, 'A')

    def test_get_proposition_with_faculty_refusal_reason(self):
        self.admission.fac_refusal_certificate = ['uuid-fac-refusal-certificate']

        # Choose an existing reason
        chosen_reason = RefusalReasonFactory()
        self.admission.refusal_reasons.add(chosen_reason)
        self.admission.other_refusal_reasons = []
        self.admission.save()

        result = self._get_command_result()
        self.assertEqual([str(result.certificat_refus_fac[0])], self.admission.fac_refusal_certificate)
        self.assertEqual(len(result.motifs_refus), 1)
        self.assertEqual(result.motifs_refus[0].motif, chosen_reason.name)
        self.assertEqual(result.motifs_refus[0].categorie, chosen_reason.category.name)

        # Choose a free reason
        self.admission.refusal_reasons.all().delete()
        self.admission.other_refusal_reasons = ['other reason']
        self.admission.save()

        result = self._get_command_result()
        self.assertEqual(len(result.motifs_refus), 1)
        self.assertEqual(result.motifs_refus[0].motif, 'other reason')
        self.assertEqual(result.motifs_refus[0].categorie, pgettext('admission', 'Other reasons'))

    def test_get_proposition_with_faculty_approval_reason(self):
        # Approval data
        self.admission.fac_approval_certificate = ['uuid-fac-approval-certificate']
        self.admission.with_additional_approval_conditions = True
        self.admission.additional_approval_conditions.set(
            [
                AdditionalApprovalConditionFactory(),
                AdditionalApprovalConditionFactory(),
            ]
        )
        free_conditions = [
            DoctorateFreeAdditionalApprovalConditionFactory(
                admission=self.admission,
                name_fr='Ma première condition',
                name_en='My first condition',
            ),
            DoctorateFreeAdditionalApprovalConditionFactory(
                admission=self.admission,
                name_fr='Ma deuxième condition',
                name_en='My second condition',
            ),
        ]
        self.admission.other_training_accepted_by_fac = DoctorateFactory(
            academic_year__current=True,
            enrollment_campus__name='Mons',
            enrollment_campus__organization__type=MAIN,
        )

        self.admission.with_prerequisite_courses = True
        self.admission.prerequisite_courses.set(
            [
                LearningUnitYearFactory(),
                LearningUnitYearFactory(),
            ]
        )
        self.admission.prerequisite_courses_fac_comment = 'My comment about the additional trainings'
        self.admission.program_planned_years_number = 3
        self.admission.annual_program_contact_person_name = 'John Doe'
        self.admission.annual_program_contact_person_email = 'john.doe@example.com'
        self.admission.join_program_fac_comment = 'My comment about the join program'

        self.admission.save()

        result = self._get_command_result()
        self.assertEqual([str(result.certificat_approbation_fac[0])], self.admission.fac_approval_certificate)

        self.assertIsNotNone(result.autre_formation_choisie_fac)
        self.assertEqual(
            result.autre_formation_choisie_fac,
            BaseFormationDTO(
                sigle=self.admission.other_training_accepted_by_fac.acronym,
                annee=self.admission.other_training_accepted_by_fac.academic_year.year,
                intitule=self.admission.other_training_accepted_by_fac.title,
                uuid=self.admission.other_training_accepted_by_fac.uuid,
                lieu_enseignement=(
                    EducationGroupVersion.objects.filter(offer=self.admission.other_training_accepted_by_fac)
                    .first()
                    .root_group.main_teaching_campus.name
                ),
            ),
        )

        self.assertEqual(result.avec_conditions_complementaires, self.admission.with_additional_approval_conditions)

        self.assertCountEqual(
            result.conditions_complementaires,
            [
                ConditionComplementaireApprobationDTO(
                    uuid=condition.uuid,
                    libre=False,
                    nom_fr=condition.name_fr,
                    nom_en=condition.name_en,
                    uuid_experience='',
                )
                for condition in self.admission.additional_approval_conditions.all()
            ]
            + [
                ConditionComplementaireApprobationDTO(
                    uuid=condition.uuid,
                    libre=True,
                    nom_fr=condition.name_fr,
                    nom_en=condition.name_en,
                    uuid_experience='',
                )
                for condition in free_conditions
            ],
        )

        prerequisite_courses = self.admission.prerequisite_courses.all()
        self.assertEqual(result.avec_complements_formation, self.admission.with_prerequisite_courses)
        self.assertEqual(len(result.complements_formation), len(prerequisite_courses))
        self.assertEqual(result.commentaire_complements_formation, self.admission.prerequisite_courses_fac_comment)
        self.assertEqual(result.nombre_annees_prevoir_programme, self.admission.program_planned_years_number)
        self.assertEqual(
            result.nom_personne_contact_programme_annuel_annuel,
            self.admission.annual_program_contact_person_name,
        )
        self.assertEqual(
            result.email_personne_contact_programme_annuel_annuel,
            self.admission.annual_program_contact_person_email,
        )
        self.assertEqual(result.commentaire_programme_conjoint, self.admission.join_program_fac_comment)
