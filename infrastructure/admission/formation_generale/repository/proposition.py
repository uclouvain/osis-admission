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
from typing import List, Optional

from django.conf import settings
from django.utils.translation import get_language

from admission.auth.roles.candidate import Candidate
from admission.contrib.models import GeneralEducationAdmissionProxy, Scholarship, Accounting
from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.domain.builder.formation_identity import FormationIdentityBuilder
from admission.ddd.admission.domain.model.bourse import BourseIdentity
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutProposition
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.infrastructure.admission.domain.service.bourse import BourseTranslator
from base.models.academic_year import AcademicYear
from admission.infrastructure.admission.formation_generale.repository._comptabilite import get_accounting_from_admission
from base.models.education_group_year import EducationGroupYear
from base.models.person import Person
from osis_common.ddd.interface import ApplicationService


class PropositionRepository(IPropositionRepository):
    @classmethod
    def search(
        cls,
        entity_ids: Optional[List['PropositionIdentity']] = None,
        matricule_candidat: str = None,
        **kwargs,
    ) -> List['Proposition']:
        raise NotImplementedError

    @classmethod
    def search_dto(cls, matricule_candidat: Optional[str] = '') -> List['PropositionDTO']:
        # Default queryset
        qs = GeneralEducationAdmissionProxy.objects.all()

        # Add filters
        if matricule_candidat:
            qs = qs.filter(candidate__global_id=matricule_candidat)

        # Return dtos
        return [cls._load_dto(proposition) for proposition in qs]

    @classmethod
    def delete(cls, entity_id: 'PropositionIdentity', **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        try:
            return cls._load(GeneralEducationAdmissionProxy.objects.get(uuid=entity_id.uuid))
        except GeneralEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def save(cls, entity: 'Proposition') -> None:
        training = EducationGroupYear.objects.get(
            acronym=entity.formation_id.sigle,
            academic_year__year=entity.formation_id.annee,
        )
        candidate = Person.objects.get(global_id=entity.matricule_candidat)

        scholarships_uuids = list(
            scholarship.uuid
            for scholarship in [
                entity.bourse_double_diplome_id,
                entity.bourse_erasmus_mundus_id,
                entity.bourse_internationale_id,
            ]
            if scholarship
        )

        if scholarships_uuids:
            scholarships = {
                scholarship.type: scholarship
                for scholarship in Scholarship.objects.filter(
                    uuid__in=scholarships_uuids,
                )
            }
        else:
            scholarships = {}

        admission, _ = GeneralEducationAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'candidate': candidate,
                'training': training,
                'determined_academic_year': (
                    entity.annee_calculee and AcademicYear.objects.get(year=entity.annee_calculee)
                ),
                'determined_pool': entity.pot_calcule,
                'double_degree_scholarship': scholarships.get(TypeBourse.DOUBLE_TRIPLE_DIPLOMATION.name),
                'international_scholarship': scholarships.get(TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name),
                'erasmus_mundus_scholarship': scholarships.get(TypeBourse.ERASMUS_MUNDUS.name),
                'is_belgian_bachelor': entity.est_bachelier_belge,
                'is_external_reorientation': entity.est_reorientation_inscription_externe,
                'regular_registration_proof': entity.attestation_inscription_reguliere,
                'is_external_modification': entity.est_modification_inscription_externe,
                'registration_change_form': entity.formulaire_modification_inscription,
                'is_non_resident': entity.est_non_resident_au_sens_decret,
                'status': entity.statut.name,
                'specific_question_answers': entity.reponses_questions_specifiques,
                'bachelor_cycle_continuation': entity.continuation_cycle_bachelier,
                'bachelor_cycle_continuation_certificate': entity.attestation_continuation_cycle_bachelier,
                'curriculum': entity.curriculum,
                'diploma_equivalence': entity.equivalence_diplome,
                'confirmation_elements': entity.elements_confirmation,
            },
        )

        Candidate.objects.get_or_create(person=candidate)
        cls._sauvegarder_comptabilite(admission, entity)

    @classmethod
    def _sauvegarder_comptabilite(cls, admission, entity):
        fr_study_allowance_application = entity.comptabilite.demande_allocation_d_etudes_communaute_francaise_belgique
        unemployment_benefit_pension_proof = entity.comptabilite.preuve_allocations_chomage_pension_indemnite
        parent_annex_25_26 = entity.comptabilite.annexe_25_26_refugies_apatrides_decision_protection_parent
        Accounting.objects.update_or_create(
            admission=admission,
            defaults={
                'institute_absence_debts_certificate': entity.comptabilite.attestation_absence_dette_etablissement,
                'french_community_study_allowance_application': fr_study_allowance_application,
                'is_staff_child': entity.comptabilite.enfant_personnel,
                'staff_child_certificate': entity.comptabilite.attestation_enfant_personnel,
                'assimilation_situation': entity.comptabilite.type_situation_assimilation.name
                if entity.comptabilite.type_situation_assimilation
                else '',
                'assimilation_1_situation_type': entity.comptabilite.sous_type_situation_assimilation_1.name
                if entity.comptabilite.sous_type_situation_assimilation_1
                else '',
                'long_term_resident_card': entity.comptabilite.carte_resident_longue_duree,
                'cire_unlimited_stay_foreigner_card': entity.comptabilite.carte_cire_sejour_illimite_etranger,
                'ue_family_member_residence_card': entity.comptabilite.carte_sejour_membre_ue,
                'ue_family_member_permanent_residence_card': entity.comptabilite.carte_sejour_permanent_membre_ue,
                'assimilation_2_situation_type': entity.comptabilite.sous_type_situation_assimilation_2.name
                if entity.comptabilite.sous_type_situation_assimilation_2
                else '',
                'refugee_a_b_card': entity.comptabilite.carte_a_b_refugie,
                'refugees_stateless_annex_25_26': entity.comptabilite.annexe_25_26_refugies_apatrides,
                'registration_certificate': entity.comptabilite.attestation_immatriculation,
                'a_b_card': entity.comptabilite.carte_a_b,
                'subsidiary_protection_decision': entity.comptabilite.decision_protection_subsidiaire,
                'temporary_protection_decision': entity.comptabilite.decision_protection_temporaire,
                'assimilation_3_situation_type': entity.comptabilite.sous_type_situation_assimilation_3.name
                if entity.comptabilite.sous_type_situation_assimilation_3
                else '',
                'professional_3_month_residence_permit': entity.comptabilite.titre_sejour_3_mois_professionel,
                'salary_slips': entity.comptabilite.fiches_remuneration,
                'replacement_3_month_residence_permit': entity.comptabilite.titre_sejour_3_mois_remplacement,
                'unemployment_benefit_pension_compensation_proof': unemployment_benefit_pension_proof,
                'cpas_certificate': entity.comptabilite.attestation_cpas,
                'relationship': entity.comptabilite.relation_parente.name
                if entity.comptabilite.relation_parente
                else '',
                'assimilation_5_situation_type': entity.comptabilite.sous_type_situation_assimilation_5.name
                if entity.comptabilite.sous_type_situation_assimilation_5
                else '',
                'household_composition_or_birth_certificate': entity.comptabilite.composition_menage_acte_naissance,
                'tutorship_act': entity.comptabilite.acte_tutelle,
                'household_composition_or_marriage_certificate': entity.comptabilite.composition_menage_acte_mariage,
                'legal_cohabitation_certificate': entity.comptabilite.attestation_cohabitation_legale,
                'parent_identity_card': entity.comptabilite.carte_identite_parent,
                'parent_long_term_residence_permit': entity.comptabilite.titre_sejour_longue_duree_parent,
                'parent_refugees_stateless_annex_25_26_or_protection_decision': parent_annex_25_26,
                'parent_3_month_residence_permit': entity.comptabilite.titre_sejour_3_mois_parent,
                'parent_salary_slips': entity.comptabilite.fiches_remuneration_parent,
                'parent_cpas_certificate': entity.comptabilite.attestation_cpas_parent,
                'assimilation_6_situation_type': entity.comptabilite.sous_type_situation_assimilation_6.name
                if entity.comptabilite.sous_type_situation_assimilation_6
                else '',
                'cfwb_scholarship_decision': entity.comptabilite.decision_bourse_cfwb,
                'scholarship_certificate': entity.comptabilite.attestation_boursier,
                'ue_long_term_stay_identity_document': entity.comptabilite.titre_identite_sejour_longue_duree_ue,
                'belgium_residence_permit': entity.comptabilite.titre_sejour_belgique,
                'sport_affiliation': entity.comptabilite.affiliation_sport.name
                if entity.comptabilite.affiliation_sport
                else '',
                'solidarity_student': entity.comptabilite.etudiant_solidaire,
                'account_number_type': entity.comptabilite.type_numero_compte.name
                if entity.comptabilite.type_numero_compte
                else '',
                'iban_account_number': entity.comptabilite.numero_compte_iban,
                'valid_iban': entity.comptabilite.iban_valide,
                'other_format_account_number': entity.comptabilite.numero_compte_autre_format,
                'bic_swift_code': entity.comptabilite.code_bic_swift_banque,
                'account_holder_first_name': entity.comptabilite.prenom_titulaire_compte,
                'account_holder_last_name': entity.comptabilite.nom_titulaire_compte,
            },
        )

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        try:
            return cls._load_dto(GeneralEducationAdmissionProxy.objects.get(uuid=entity_id.uuid))
        except GeneralEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def _load(cls, admission: 'GeneralEducationAdmission') -> 'Proposition':
        return Proposition(
            entity_id=PropositionIdentityBuilder().build_from_uuid(admission.uuid),
            matricule_candidat=admission.candidate.global_id,
            creee_le=admission.created,
            modifiee_le=admission.modified,
            formation_id=FormationIdentityBuilder.build(
                sigle=admission.training.acronym,
                annee=admission.training.academic_year.year,
            ),
            annee_calculee=admission.determined_academic_year and admission.determined_academic_year.year,
            pot_calcule=admission.determined_pool,
            statut=ChoixStatutProposition[admission.status],
            bourse_internationale_id=BourseIdentity(uuid=str(admission.international_scholarship.uuid))
            if admission.international_scholarship
            else None,
            bourse_double_diplome_id=BourseIdentity(uuid=str(admission.double_degree_scholarship.uuid))
            if admission.double_degree_scholarship
            else None,
            bourse_erasmus_mundus_id=BourseIdentity(uuid=str(admission.erasmus_mundus_scholarship.uuid))
            if admission.erasmus_mundus_scholarship
            else None,
            reponses_questions_specifiques=admission.specific_question_answers,
            est_bachelier_belge=admission.is_belgian_bachelor,
            est_reorientation_inscription_externe=admission.is_external_reorientation,
            attestation_inscription_reguliere=admission.regular_registration_proof,
            est_modification_inscription_externe=admission.is_external_modification,
            formulaire_modification_inscription=admission.registration_change_form,
            est_non_resident_au_sens_decret=admission.is_non_resident,
            curriculum=admission.curriculum,
            equivalence_diplome=admission.diploma_equivalence,
            continuation_cycle_bachelier=admission.bachelor_cycle_continuation,
            attestation_continuation_cycle_bachelier=admission.bachelor_cycle_continuation_certificate,
            comptabilite=get_accounting_from_admission(admission=admission),
            elements_confirmation=admission.confirmation_elements,
        )

    @classmethod
    def _load_dto(cls, admission: GeneralEducationAdmission) -> 'PropositionDTO':
        return PropositionDTO(
            uuid=admission.uuid,
            creee_le=admission.created,
            modifiee_le=admission.modified,
            erreurs=admission.detailed_status or [],
            statut=admission.status,
            annee_calculee=admission.determined_academic_year and admission.determined_academic_year.year,
            pot_calcule=admission.determined_pool or '',
            date_fin_pot=admission.pool_end_date,  # from annotation
            formation=FormationDTO(
                sigle=admission.training.acronym,
                annee=admission.training.academic_year.year,
                intitule=admission.training.title
                if get_language() == settings.LANGUAGE_CODE
                else admission.training.title_english,
                campus=admission.teaching_campus or '',
                type=admission.training.education_group_type.name,
                code_domaine=admission.training.main_domain.code if admission.training.main_domain else '',
            ),
            matricule_candidat=admission.candidate.global_id,
            prenom_candidat=admission.candidate.first_name,
            nom_candidat=admission.candidate.last_name,
            bourse_double_diplome=BourseTranslator.build_dto(admission.double_degree_scholarship)
            if admission.double_degree_scholarship
            else None,
            bourse_internationale=BourseTranslator.build_dto(admission.international_scholarship)
            if admission.international_scholarship
            else None,
            bourse_erasmus_mundus=BourseTranslator.build_dto(admission.erasmus_mundus_scholarship)
            if admission.erasmus_mundus_scholarship
            else None,
            reponses_questions_specifiques=admission.specific_question_answers,
            curriculum=admission.curriculum,
            equivalence_diplome=admission.diploma_equivalence,
            continuation_cycle_bachelier=admission.bachelor_cycle_continuation,
            attestation_continuation_cycle_bachelier=admission.bachelor_cycle_continuation_certificate,
        )
