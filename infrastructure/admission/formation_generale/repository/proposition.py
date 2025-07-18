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

from contextlib import suppress
from enum import Enum
from typing import List, Optional, Union

import attrs
from django.conf import settings
from django.db import transaction
from django.db.models import Case, IntegerField, OuterRef, Prefetch, Subquery, When
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, pgettext
from osis_history.models import HistoryEntry

from admission.auth.roles.candidate import Candidate
from admission.ddd.admission.domain.builder.formation_identity import (
    FormationIdentityBuilder,
)
from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.model.complement_formation import (
    ComplementFormationIdentity,
)
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
    ConditionComplementaireLibreApprobation,
)
from admission.ddd.admission.domain.model.enums.equivalence import (
    EtatEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    TypeEquivalenceTitreAcces,
)
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.domain.model.poste_diplomatique import (
    PosteDiplomatiqueIdentity,
)
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import (
    IUnitesEnseignementTranslator,
)
from admission.ddd.admission.dtos.formation import (
    BaseFormationDTO,
    CampusDTO,
    FormationDTO,
)
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    DROITS_INSCRIPTION_MONTANT_VALEURS,
    STATUTS_PROPOSITION_GENERALE_SOUMISE,
    BesoinDeDerogation,
    BesoinDeDerogationDelegueVrae,
    ChoixStatutPropositionGenerale,
    DerogationFinancement,
    PoursuiteDeCycle,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition,
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    StatutChecklist,
    StatutsChecklistGenerale,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PremierePropositionSoumisesNonTrouveeException,
    PropositionNonTrouveeException,
)
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.formation_generale.dtos.condition_approbation import (
    ConditionComplementaireApprobationDTO,
)
from admission.ddd.admission.formation_generale.dtos.motif_refus import MotifRefusDTO
from admission.ddd.admission.formation_generale.dtos.proposition import (
    PropositionGestionnaireDTO,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)
from admission.infrastructure.admission.domain.service.poste_diplomatique import (
    PosteDiplomatiqueTranslator,
)
from admission.infrastructure.admission.formation_generale.repository._comptabilite import (
    get_accounting_from_admission,
)
from admission.infrastructure.admission.repository.proposition import (
    GlobalPropositionRepository,
)
from admission.infrastructure.utils import dto_to_dict
from admission.models import Accounting, GeneralEducationAdmissionProxy
from admission.models.checklist import FreeAdditionalApprovalCondition, RefusalReason
from admission.models.general_education import GeneralEducationAdmission
from base.models.academic_year import AcademicYear
from base.models.campus import Campus as CampusDb
from base.models.education_group_year import EducationGroupYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.financabilite.domain.model.enums.situation import SituationFinancabilite
from ddd.logic.learning_unit.dtos import LearningUnitSearchDTO, PartimSearchDTO
from ddd.logic.reference.domain.model.bourse import BourseIdentity
from epc.models.enums.condition_acces import ConditionAcces
from infrastructure.reference.domain.service.bourse import BourseTranslator
from osis_common.ddd.interface import ApplicationService
from reference.models.enums.scholarship_type import ScholarshipType
from reference.models.scholarship import Scholarship


class PropositionRepository(GlobalPropositionRepository, IPropositionRepository):
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
        qs = GeneralEducationAdmissionProxy.objects.for_dto().all()

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
            return cls._load(
                GeneralEducationAdmissionProxy.objects.prefetch_related(
                    'additional_approval_conditions',
                    'freeadditionalapprovalcondition_set',
                    'prerequisite_courses',
                    'refusal_reasons',
                )
                .select_related(
                    'other_training_accepted_by_fac__academic_year',
                    'admission_requirement_year',
                    'last_update_author',
                )
                .get(uuid=entity_id.uuid)
            )
        except GeneralEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def _serialize(cls, inst, field, value):
        if isinstance(value, StatutChecklist):
            return attrs.asdict(value, value_serializer=cls._serialize)

        if isinstance(value, Enum):
            return value.name

        return value

    @classmethod
    def save(cls, entity: 'Proposition', mise_a_jour_date_derniere_modification=True) -> None:
        training = EducationGroupYear.objects.get(
            acronym=entity.formation_id.sigle,
            academic_year__year=entity.formation_id.annee,
        )
        other_training = (
            EducationGroupYear.objects.get(
                acronym=entity.autre_formation_choisie_fac_id.sigle,
                academic_year__year=entity.autre_formation_choisie_fac_id.annee,
            )
            if entity.autre_formation_choisie_fac_id
            else None
        )

        persons = {
            person.global_id: person
            for person in Person.objects.filter(
                global_id__in=[
                    matricule
                    for matricule in [
                        entity.matricule_candidat,
                        entity.auteur_derniere_modification,
                        entity.financabilite_derogation_premiere_notification_par,
                        entity.financabilite_derogation_derniere_notification_par,
                        entity.financabilite_etabli_par,
                    ]
                    if matricule
                ]
            )
        }

        last_update_author_person = (
            persons[entity.auteur_derniere_modification] if entity.auteur_derniere_modification in persons else None
        )

        candidate = persons[entity.matricule_candidat]

        financabilite_etabli_par_person = (
            persons[entity.financabilite_etabli_par] if entity.financabilite_etabli_par in persons else None
        )

        financabilite_derogation_premiere_notification_par_person = (
            persons[entity.financabilite_derogation_premiere_notification_par]
            if entity.financabilite_derogation_premiere_notification_par in persons
            else None
        )

        financabilite_derogation_derniere_notification_par_person = (
            persons[entity.financabilite_derogation_derniere_notification_par]
            if entity.financabilite_derogation_derniere_notification_par in persons
            else None
        )

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

        years = [year for year in [entity.annee_calculee, entity.millesime_condition_acces] if year]
        academic_years = {}

        if years:
            academic_years = {year.year: year for year in AcademicYear.objects.filter(year__in=years)}

        # FIXME remove when upgrading to Django 5.2? https://code.djangoproject.com/ticket/35890
        modified_at_fields = {'modified_at': timezone.now()} if mise_a_jour_date_derniere_modification else {}

        admission, _ = GeneralEducationAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                **modified_at_fields,
                'candidate': candidate,
                'training': training,
                'determined_academic_year': entity.annee_calculee and academic_years[entity.annee_calculee],
                'determined_pool': entity.pot_calcule and entity.pot_calcule.name,
                'reference': entity.reference,
                'type_demande': entity.type_demande.name,
                'submitted_at': entity.soumise_le,
                'has_double_degree_scholarship': entity.avec_bourse_double_diplome,
                'double_degree_scholarship': scholarships.get(ScholarshipType.DOUBLE_TRIPLE_DIPLOMATION.name),
                'has_international_scholarship': entity.avec_bourse_internationale,
                'international_scholarship': scholarships.get(
                    ScholarshipType.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name
                ),
                'has_erasmus_mundus_scholarship': entity.avec_bourse_erasmus_mundus,
                'erasmus_mundus_scholarship': scholarships.get(ScholarshipType.ERASMUS_MUNDUS.name),
                'is_belgian_bachelor': entity.est_bachelier_belge,
                'is_external_reorientation': entity.est_reorientation_inscription_externe,
                'regular_registration_proof': entity.attestation_inscription_reguliere,
                'reorientation_form': entity.formulaire_reorientation,
                'is_external_modification': entity.est_modification_inscription_externe,
                'registration_change_form': entity.formulaire_modification_inscription,
                'regular_registration_proof_for_registration_change': (
                    entity.attestation_inscription_reguliere_pour_modification_inscription
                ),
                'is_non_resident': entity.est_non_resident_au_sens_decret,
                'status': entity.statut.name,
                'specific_question_answers': entity.reponses_questions_specifiques,
                'curriculum': entity.curriculum,
                'diploma_equivalence': entity.equivalence_diplome,
                'confirmation_elements': entity.elements_confirmation,
                'late_enrollment': entity.est_inscription_tardive,
                'submitted_profile': entity.profil_soumis_candidat.to_dict() if entity.profil_soumis_candidat else {},
                'checklist': {
                    'initial': entity.checklist_initiale
                    and attrs.asdict(entity.checklist_initiale, value_serializer=cls._serialize)
                    or {},
                    'current': entity.checklist_actuelle
                    and attrs.asdict(entity.checklist_actuelle, value_serializer=cls._serialize)
                    or {},
                },
                'cycle_pursuit': entity.poursuite_de_cycle.name,
                'financability_computed_rule': (
                    entity.financabilite_regle_calcule.name if entity.financabilite_regle_calcule else ''
                ),
                'financability_computed_rule_situation': (
                    entity.financabilite_regle_calcule_situation.name
                    if entity.financabilite_regle_calcule_situation
                    else ''
                ),
                'financability_computed_rule_on': entity.financabilite_regle_calcule_le,
                'financability_rule': entity.financabilite_regle.name if entity.financabilite_regle else '',
                'financability_established_by': financabilite_etabli_par_person,
                'financability_established_on': entity.financabilite_etabli_le,
                'financability_dispensation_status': (
                    entity.financabilite_derogation_statut.name if entity.financabilite_derogation_statut else ''
                ),
                'financabilite_dispensation_vrae': entity.financabilite_derogation_vrae,
                'financability_dispensation_first_notification_on': (
                    entity.financabilite_derogation_premiere_notification_le
                ),
                'financability_dispensation_first_notification_by': (
                    financabilite_derogation_premiere_notification_par_person
                ),
                'financability_dispensation_last_notification_on': (
                    entity.financabilite_derogation_derniere_notification_le
                ),
                'financability_dispensation_last_notification_by': (
                    financabilite_derogation_derniere_notification_par_person
                ),
                'last_update_author': last_update_author_person,
                'fac_approval_certificate': entity.certificat_approbation_fac,
                'fac_refusal_certificate': entity.certificat_refus_fac,
                'delegate_vrae_dispensation': (
                    entity.derogation_delegue_vrae.name if entity.derogation_delegue_vrae else ''
                ),
                'delegate_vrae_dispensation_comment': entity.derogation_delegue_vrae_commentaire,
                'delegate_vrae_dispensation_certificate': entity.justificatif_derogation_delegue_vrae,
                'sic_approval_certificate': entity.certificat_approbation_sic,
                'sic_annexe_approval_certificate': entity.certificat_approbation_sic_annexe,
                'sic_refusal_certificate': entity.certificat_refus_sic,
                'other_refusal_reasons': entity.autres_motifs_refus,
                'other_training_accepted_by_fac': other_training,
                'with_additional_approval_conditions': entity.avec_conditions_complementaires,
                'with_prerequisite_courses': entity.avec_complements_formation,
                'prerequisite_courses_fac_comment': entity.commentaire_complements_formation,
                'program_planned_years_number': entity.nombre_annees_prevoir_programme,
                'annual_program_contact_person_name': entity.nom_personne_contact_programme_annuel_annuel,
                'annual_program_contact_person_email': entity.email_personne_contact_programme_annuel_annuel,
                'join_program_fac_comment': entity.commentaire_programme_conjoint,
                'additional_documents': entity.documents_additionnels,
                'requested_documents_deadline': entity.echeance_demande_documents,
                'diplomatic_post_id': entity.poste_diplomatique.code if entity.poste_diplomatique else None,
                'admission_requirement': entity.condition_acces.name if entity.condition_acces else '',
                'admission_requirement_year': entity.millesime_condition_acces
                and academic_years[entity.millesime_condition_acces],
                'foreign_access_title_equivalency_type': (
                    entity.type_equivalence_titre_acces.name if entity.type_equivalence_titre_acces else ''
                ),
                'foreign_access_title_equivalency_restriction_about': entity.information_a_propos_de_la_restriction,
                'foreign_access_title_equivalency_status': (
                    entity.statut_equivalence_titre_acces.name if entity.statut_equivalence_titre_acces else ''
                ),
                'foreign_access_title_equivalency_state': (
                    entity.etat_equivalence_titre_acces.name if entity.etat_equivalence_titre_acces else ''
                ),
                'foreign_access_title_equivalency_effective_date': entity.date_prise_effet_equivalence_titre_acces,
                'dispensation_needed': entity.besoin_de_derogation.name if entity.besoin_de_derogation else '',
                'tuition_fees_amount': entity.droits_inscription_montant,
                'tuition_fees_amount_other': entity.droits_inscription_montant_autre,
                'tuition_fees_dispensation': entity.dispense_ou_droits_majores,
                'particular_cost': entity.tarif_particulier,
                'rebilling_or_third_party_payer': entity.refacturation_ou_tiers_payant,
                'first_year_inscription_and_status': entity.annee_de_premiere_inscription_et_statut,
                'is_mobility': entity.est_mobilite,
                'mobility_months_amount': entity.nombre_de_mois_de_mobilite,
                'must_report_to_sic': entity.doit_se_presenter_en_sic,
                'communication_to_the_candidate': entity.communication_au_candidat,
                'refusal_type': entity.type_de_refus,
                'must_provide_student_visa_d': entity.doit_fournir_visa_etudes,
                'student_visa_d': entity.visa_etudes_d,
                'signed_enrollment_authorization': entity.certificat_autorisation_signe,
            },
        )

        Candidate.objects.get_or_create(person=candidate)
        cls._sauvegarder_comptabilite(admission, entity)

        admission.additional_approval_conditions.set([c.uuid for c in entity.conditions_complementaires_existantes])
        admission.prerequisite_courses.set([training.uuid for training in entity.complements_formation])
        admission.refusal_reasons.set([motif.uuid for motif in entity.motifs_refus])
        with transaction.atomic():
            admission.freeadditionalapprovalcondition_set.all().delete()
            FreeAdditionalApprovalCondition.objects.bulk_create(
                [
                    FreeAdditionalApprovalCondition(
                        name_fr=condition.nom_fr,
                        name_en=condition.nom_en,
                        related_experience_id=condition.uuid_experience,
                        admission=admission,
                    )
                    for condition in entity.conditions_complementaires_libres
                ],
            )

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
                'assimilation_situation': (
                    entity.comptabilite.type_situation_assimilation.name
                    if entity.comptabilite.type_situation_assimilation
                    else ''
                ),
                'assimilation_1_situation_type': (
                    entity.comptabilite.sous_type_situation_assimilation_1.name
                    if entity.comptabilite.sous_type_situation_assimilation_1
                    else ''
                ),
                'long_term_resident_card': entity.comptabilite.carte_resident_longue_duree,
                'cire_unlimited_stay_foreigner_card': entity.comptabilite.carte_cire_sejour_illimite_etranger,
                'ue_family_member_residence_card': entity.comptabilite.carte_sejour_membre_ue,
                'ue_family_member_permanent_residence_card': entity.comptabilite.carte_sejour_permanent_membre_ue,
                'assimilation_2_situation_type': (
                    entity.comptabilite.sous_type_situation_assimilation_2.name
                    if entity.comptabilite.sous_type_situation_assimilation_2
                    else ''
                ),
                'refugee_a_b_card': entity.comptabilite.carte_a_b_refugie,
                'refugees_stateless_annex_25_26': entity.comptabilite.annexe_25_26_refugies_apatrides,
                'registration_certificate': entity.comptabilite.attestation_immatriculation,
                'stateless_person_proof': entity.comptabilite.preuve_statut_apatride,
                'a_b_card': entity.comptabilite.carte_a_b,
                'subsidiary_protection_decision': entity.comptabilite.decision_protection_subsidiaire,
                'temporary_protection_decision': entity.comptabilite.decision_protection_temporaire,
                'a_card': entity.comptabilite.carte_a,
                'assimilation_3_situation_type': (
                    entity.comptabilite.sous_type_situation_assimilation_3.name
                    if entity.comptabilite.sous_type_situation_assimilation_3
                    else ''
                ),
                'professional_3_month_residence_permit': entity.comptabilite.titre_sejour_3_mois_professionel,
                'salary_slips': entity.comptabilite.fiches_remuneration,
                'replacement_3_month_residence_permit': entity.comptabilite.titre_sejour_3_mois_remplacement,
                'unemployment_benefit_pension_compensation_proof': unemployment_benefit_pension_proof,
                'cpas_certificate': entity.comptabilite.attestation_cpas,
                'relationship': (
                    entity.comptabilite.relation_parente.name if entity.comptabilite.relation_parente else ''
                ),
                'assimilation_5_situation_type': (
                    entity.comptabilite.sous_type_situation_assimilation_5.name
                    if entity.comptabilite.sous_type_situation_assimilation_5
                    else ''
                ),
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
                'assimilation_6_situation_type': (
                    entity.comptabilite.sous_type_situation_assimilation_6.name
                    if entity.comptabilite.sous_type_situation_assimilation_6
                    else ''
                ),
                'cfwb_scholarship_decision': entity.comptabilite.decision_bourse_cfwb,
                'scholarship_certificate': entity.comptabilite.attestation_boursier,
                'ue_long_term_stay_identity_document': entity.comptabilite.titre_identite_sejour_longue_duree_ue,
                'belgium_residence_permit': entity.comptabilite.titre_sejour_belgique,
                'sport_affiliation': (
                    entity.comptabilite.affiliation_sport.name if entity.comptabilite.affiliation_sport else ''
                ),
                'solidarity_student': entity.comptabilite.etudiant_solidaire,
                'account_number_type': (
                    entity.comptabilite.type_numero_compte.name if entity.comptabilite.type_numero_compte else ''
                ),
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
            return cls._load_dto(GeneralEducationAdmissionProxy.objects.for_dto().get(uuid=entity_id.uuid))
        except GeneralEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def _load(cls, admission: 'GeneralEducationAdmission') -> 'Proposition':
        checklist_initiale = admission.checklist.get('initial')
        checklist_actuelle = admission.checklist.get('current')

        return Proposition(
            entity_id=PropositionIdentityBuilder().build_from_uuid(str(admission.uuid)),
            matricule_candidat=admission.candidate.global_id,
            creee_le=admission.created_at,
            modifiee_le=admission.modified_at,
            reference=admission.reference,
            formation_id=FormationIdentityBuilder.build(
                sigle=admission.training.acronym,
                annee=admission.training.academic_year.year,
            ),
            type_demande=TypeDemande[admission.type_demande],
            soumise_le=admission.submitted_at,
            annee_calculee=admission.determined_academic_year and admission.determined_academic_year.year,
            pot_calcule=admission.determined_pool and AcademicCalendarTypes[admission.determined_pool],
            statut=ChoixStatutPropositionGenerale[admission.status],
            avec_bourse_internationale=admission.has_international_scholarship,
            bourse_internationale_id=(
                BourseIdentity(uuid=str(admission.international_scholarship.uuid))
                if admission.international_scholarship
                else None
            ),
            avec_bourse_double_diplome=admission.has_double_degree_scholarship,
            bourse_double_diplome_id=(
                BourseIdentity(uuid=str(admission.double_degree_scholarship.uuid))
                if admission.double_degree_scholarship
                else None
            ),
            avec_bourse_erasmus_mundus=admission.has_erasmus_mundus_scholarship,
            bourse_erasmus_mundus_id=(
                BourseIdentity(uuid=str(admission.erasmus_mundus_scholarship.uuid))
                if admission.erasmus_mundus_scholarship
                else None
            ),
            reponses_questions_specifiques=admission.specific_question_answers,
            est_bachelier_belge=admission.is_belgian_bachelor,
            est_reorientation_inscription_externe=admission.is_external_reorientation,
            attestation_inscription_reguliere=admission.regular_registration_proof,
            attestation_inscription_reguliere_pour_modification_inscription=(
                admission.regular_registration_proof_for_registration_change
            ),
            formulaire_reorientation=admission.reorientation_form,
            est_modification_inscription_externe=admission.is_external_modification,
            formulaire_modification_inscription=admission.registration_change_form,
            est_non_resident_au_sens_decret=admission.is_non_resident,
            curriculum=admission.curriculum,
            equivalence_diplome=admission.diploma_equivalence,
            comptabilite=get_accounting_from_admission(admission=admission),
            elements_confirmation=admission.confirmation_elements,
            est_inscription_tardive=admission.late_enrollment,
            profil_soumis_candidat=(
                ProfilCandidat.from_dict(admission.submitted_profile) if admission.submitted_profile else None
            ),
            documents_demandes=admission.requested_documents,
            echeance_demande_documents=admission.requested_documents_deadline,
            checklist_initiale=checklist_initiale and StatutsChecklistGenerale.from_dict(checklist_initiale),
            checklist_actuelle=checklist_actuelle and StatutsChecklistGenerale.from_dict(checklist_actuelle),
            type_de_refus=admission.refusal_type,
            motifs_refus=[MotifRefusIdentity(uuid=motif.uuid) for motif in admission.refusal_reasons.all()],
            autres_motifs_refus=admission.other_refusal_reasons,
            financabilite_regle_calcule=(
                EtatFinancabilite[admission.financability_computed_rule]
                if admission.financability_computed_rule
                else ''
            ),
            financabilite_regle_calcule_situation=(
                SituationFinancabilite[admission.financability_computed_rule_situation]
                if admission.financability_computed_rule_situation
                else ''
            ),
            financabilite_regle_calcule_le=admission.financability_computed_rule_on,
            financabilite_regle=(
                SituationFinancabilite[admission.financability_rule] if admission.financability_rule else ''
            ),
            financabilite_etabli_par=(
                admission.financability_established_by.global_id if admission.financability_established_by else None
            ),
            financabilite_etabli_le=admission.financability_established_on,
            financabilite_derogation_statut=(
                DerogationFinancement[admission.financability_dispensation_status]
                if admission.financability_dispensation_status
                else ''
            ),
            financabilite_derogation_vrae=admission.financabilite_dispensation_vrae,
            financabilite_derogation_premiere_notification_le=(
                admission.financability_dispensation_first_notification_on
            ),
            financabilite_derogation_premiere_notification_par=(
                admission.financability_dispensation_first_notification_by.global_id
                if admission.financability_dispensation_first_notification_by
                else None
            ),
            financabilite_derogation_derniere_notification_le=(
                admission.financability_dispensation_last_notification_on
            ),
            financabilite_derogation_derniere_notification_par=(
                admission.financability_dispensation_last_notification_by.global_id
                if admission.financability_dispensation_last_notification_by
                else None
            ),
            certificat_refus_fac=admission.fac_refusal_certificate,
            certificat_approbation_fac=admission.fac_approval_certificate,
            derogation_delegue_vrae=(
                BesoinDeDerogationDelegueVrae[admission.delegate_vrae_dispensation]
                if admission.delegate_vrae_dispensation
                else None
            ),
            derogation_delegue_vrae_commentaire=admission.delegate_vrae_dispensation_comment,
            justificatif_derogation_delegue_vrae=admission.delegate_vrae_dispensation_certificate,
            certificat_approbation_sic=admission.sic_approval_certificate,
            certificat_approbation_sic_annexe=admission.sic_annexe_approval_certificate,
            certificat_refus_sic=admission.sic_refusal_certificate,
            autre_formation_choisie_fac_id=(
                FormationIdentityBuilder.build(
                    sigle=admission.other_training_accepted_by_fac.acronym,
                    annee=admission.other_training_accepted_by_fac.academic_year.year,
                )
                if admission.other_training_accepted_by_fac_id
                else None
            ),
            avec_conditions_complementaires=admission.with_additional_approval_conditions,
            conditions_complementaires_existantes=[
                ConditionComplementaireApprobationIdentity(uuid=condition.uuid)
                for condition in admission.additional_approval_conditions.all()
            ],
            conditions_complementaires_libres=[
                ConditionComplementaireLibreApprobation(
                    nom_fr=condition.name_fr,
                    nom_en=condition.name_en,
                    uuid_experience=str(condition.related_experience_id) if condition.related_experience_id else '',
                )
                for condition in admission.freeadditionalapprovalcondition_set.all()
            ],
            avec_complements_formation=admission.with_prerequisite_courses,
            complements_formation=[
                ComplementFormationIdentity(uuid=admission_training.uuid)
                for admission_training in admission.prerequisite_courses.all()
            ],
            commentaire_complements_formation=admission.prerequisite_courses_fac_comment,
            nombre_annees_prevoir_programme=admission.program_planned_years_number,
            nom_personne_contact_programme_annuel_annuel=admission.annual_program_contact_person_name,
            email_personne_contact_programme_annuel_annuel=admission.annual_program_contact_person_email,
            commentaire_programme_conjoint=admission.join_program_fac_comment,
            documents_additionnels=admission.additional_documents,
            poste_diplomatique=(
                PosteDiplomatiqueIdentity(code=admission.diplomatic_post.code) if admission.diplomatic_post else None
            ),
            condition_acces=(
                ConditionAcces[admission.admission_requirement] if admission.admission_requirement else None
            ),
            millesime_condition_acces=admission.admission_requirement_year
            and admission.admission_requirement_year.year,
            information_a_propos_de_la_restriction=admission.foreign_access_title_equivalency_restriction_about,
            type_equivalence_titre_acces=(
                TypeEquivalenceTitreAcces[admission.foreign_access_title_equivalency_type]
                if admission.foreign_access_title_equivalency_type
                else None
            ),
            statut_equivalence_titre_acces=(
                StatutEquivalenceTitreAcces[admission.foreign_access_title_equivalency_status]
                if admission.foreign_access_title_equivalency_status
                else None
            ),
            etat_equivalence_titre_acces=(
                EtatEquivalenceTitreAcces[admission.foreign_access_title_equivalency_state]
                if admission.foreign_access_title_equivalency_state
                else None
            ),
            date_prise_effet_equivalence_titre_acces=admission.foreign_access_title_equivalency_effective_date,
            besoin_de_derogation=(
                BesoinDeDerogation[admission.dispensation_needed] if admission.dispensation_needed else ''
            ),
            droits_inscription_montant=admission.tuition_fees_amount,
            droits_inscription_montant_autre=admission.tuition_fees_amount_other,
            dispense_ou_droits_majores=admission.tuition_fees_dispensation,
            tarif_particulier=admission.particular_cost,
            refacturation_ou_tiers_payant=admission.rebilling_or_third_party_payer,
            annee_de_premiere_inscription_et_statut=admission.first_year_inscription_and_status,
            est_mobilite=admission.is_mobility,
            nombre_de_mois_de_mobilite=admission.mobility_months_amount,
            doit_se_presenter_en_sic=admission.must_report_to_sic,
            communication_au_candidat=admission.communication_to_the_candidate,
            poursuite_de_cycle=(
                PoursuiteDeCycle[admission.cycle_pursuit]
                if admission.cycle_pursuit
                else PoursuiteDeCycle.TO_BE_DETERMINED
            ),
            poursuite_de_cycle_a_specifier=admission.training.education_group_type.name == TrainingType.BACHELOR.name,
            auteur_derniere_modification=admission.last_update_author.global_id if admission.last_update_author else '',
            doit_fournir_visa_etudes=admission.must_provide_student_visa_d,
            visa_etudes_d=admission.student_visa_d,
            certificat_autorisation_signe=admission.signed_enrollment_authorization,
        )

    @classmethod
    def _load_dto(cls, admission: GeneralEducationAdmission) -> 'PropositionDTO':
        campus = (
            CampusDb.objects.select_related('country')
            .filter(
                teaching_campus__educationgroupversion__version_name='',
                teaching_campus__educationgroupversion__transition_name='',
                teaching_campus__educationgroupversion__offer_id=admission.training_id,
            )
            .first()
        )

        return PropositionDTO(
            uuid=admission.uuid,
            creee_le=admission.created_at,
            modifiee_le=admission.modified_at,
            reference=admission.formatted_reference,
            soumise_le=admission.submitted_at,
            erreurs=admission.detailed_status or [],
            statut=admission.status,
            annee_calculee=admission.determined_academic_year and admission.determined_academic_year.year,
            pot_calcule=admission.determined_pool or '',
            date_fin_pot=admission.pool_end_date,  # from annotation
            formation=FormationDTO(
                sigle=admission.training.acronym,
                code=admission.training.partial_acronym,
                annee=admission.training.academic_year.year,
                date_debut=admission.training.academic_year.start_date,
                intitule=(
                    admission.training.title
                    if get_language() == settings.LANGUAGE_CODE_FR
                    else admission.training.title_english
                ),
                intitule_fr=admission.training.title,
                intitule_en=admission.training.title_english,
                campus=(
                    CampusDTO(
                        uuid=campus.uuid,
                        nom=campus.name,
                        code_postal=campus.postal_code,
                        ville=campus.city,
                        pays_iso_code=campus.country.iso_code if campus.country else '',
                        nom_pays=campus.country.name if campus.country else '',
                        rue=campus.street,
                        numero_rue=campus.street_number,
                        boite_postale=campus.postal_box,
                        localisation=campus.location,
                        email_inscription_sic=campus.sic_enrollment_email,
                    )
                    if campus
                    else None
                ),
                type=admission.training.education_group_type.name,
                code_domaine=admission.training.main_domain.code if admission.training.main_domain else '',
                campus_inscription=(
                    CampusDTO(
                        uuid=admission.training.enrollment_campus.uuid,
                        nom=admission.training.enrollment_campus.name,
                        code_postal=admission.training.enrollment_campus.postal_code,
                        ville=admission.training.enrollment_campus.city,
                        pays_iso_code=(
                            admission.training.enrollment_campus.country.iso_code
                            if admission.training.enrollment_campus.country
                            else ''
                        ),
                        nom_pays=(
                            admission.training.enrollment_campus.country.name
                            if admission.training.enrollment_campus.country
                            else ''
                        ),
                        rue=admission.training.enrollment_campus.street,
                        numero_rue=admission.training.enrollment_campus.street_number,
                        boite_postale=admission.training.enrollment_campus.postal_box,
                        localisation=admission.training.enrollment_campus.location,
                        email_inscription_sic=admission.training.enrollment_campus.sic_enrollment_email,
                    )
                    if admission.training.enrollment_campus
                    else None
                ),
                sigle_entite_gestion=admission.training_management_faculty
                or admission.sigle_entite_gestion,  # from annotation
                credits=admission.training.credits,
                grade_academique=admission.training_academic_grade,  # From annotation
            ),
            matricule_candidat=admission.candidate.global_id,
            prenom_candidat=admission.candidate.first_name,
            nom_candidat=admission.candidate.last_name,
            avec_bourse_double_diplome=admission.has_double_degree_scholarship,
            bourse_double_diplome=(
                BourseTranslator.build_dto(admission.double_degree_scholarship)
                if admission.double_degree_scholarship
                else None
            ),
            avec_bourse_internationale=admission.has_international_scholarship,
            bourse_internationale=(
                BourseTranslator.build_dto(admission.international_scholarship)
                if admission.international_scholarship
                else None
            ),
            avec_bourse_erasmus_mundus=admission.has_erasmus_mundus_scholarship,
            bourse_erasmus_mundus=(
                BourseTranslator.build_dto(admission.erasmus_mundus_scholarship)
                if admission.erasmus_mundus_scholarship
                else None
            ),
            reponses_questions_specifiques=admission.specific_question_answers,
            curriculum=admission.curriculum,
            equivalence_diplome=admission.diploma_equivalence,
            est_bachelier_belge=admission.is_belgian_bachelor,
            est_non_resident_au_sens_decret=admission.is_non_resident,
            elements_confirmation=admission.confirmation_elements,
            est_modification_inscription_externe=admission.is_external_modification,
            formulaire_modification_inscription=admission.registration_change_form,
            est_reorientation_inscription_externe=admission.is_external_reorientation,
            attestation_inscription_reguliere=admission.regular_registration_proof,
            attestation_inscription_reguliere_pour_modification_inscription=(
                admission.regular_registration_proof_for_registration_change
            ),
            formulaire_reorientation=admission.reorientation_form,
            pdf_recapitulatif=admission.pdf_recap,
            documents_demandes=admission.requested_documents,
            echeance_demande_documents=admission.requested_documents_deadline,
            documents_libres_fac_uclouvain=admission.uclouvain_fac_documents,
            documents_libres_sic_uclouvain=admission.uclouvain_sic_documents,
            financabilite_regle_calcule=admission.financability_computed_rule,
            financabilite_regle_calcule_situation=admission.financability_computed_rule_situation,
            financabilite_regle_calcule_le=admission.financability_computed_rule_on,
            financabilite_regle=admission.financability_rule,
            financabilite_etabli_par=(
                admission.financability_established_by.global_id if admission.financability_established_by else None
            ),
            financabilite_etabli_le=admission.financability_established_on,
            financabilite_derogation_statut=admission.financability_dispensation_status,
            financabilite_derogation_vrae=admission.financabilite_dispensation_vrae,
            financabilite_derogation_premiere_notification_le=(
                admission.financability_dispensation_first_notification_on
            ),
            financabilite_derogation_premiere_notification_par=(
                admission.financability_dispensation_first_notification_by.global_id
                if admission.financability_dispensation_first_notification_by
                else None
            ),
            financabilite_derogation_derniere_notification_le=(
                admission.financability_dispensation_last_notification_on
            ),
            financabilite_derogation_derniere_notification_par=(
                admission.financability_dispensation_last_notification_by.global_id
                if admission.financability_dispensation_last_notification_by
                else None
            ),
            certificat_refus_fac=admission.fac_refusal_certificate,
            certificat_approbation_fac=admission.fac_approval_certificate,
            derogation_delegue_vrae=admission.delegate_vrae_dispensation,
            derogation_delegue_vrae_commentaire=admission.delegate_vrae_dispensation_comment,
            justificatif_derogation_delegue_vrae=admission.delegate_vrae_dispensation_certificate,
            certificat_approbation_sic=admission.sic_approval_certificate,
            certificat_approbation_sic_annexe=admission.sic_annexe_approval_certificate,
            certificat_refus_sic=admission.sic_refusal_certificate,
            documents_additionnels=admission.additional_documents,
            poste_diplomatique=(
                PosteDiplomatiqueTranslator.build_dto(admission.diplomatic_post) if admission.diplomatic_post else None
            ),
            doit_fournir_visa_etudes=admission.must_provide_student_visa_d,
            visa_etudes_d=admission.student_visa_d,
            certificat_autorisation_signe=admission.signed_enrollment_authorization,
            type=admission.type_demande,
        )

    @classmethod
    def _load_dto_for_gestionnaire(
        cls,
        admission: GeneralEducationAdmission,
        prerequisite_courses: List[Union['PartimSearchDTO', 'LearningUnitSearchDTO']],
    ) -> 'PropositionGestionnaireDTO':
        is_french_language = get_language() == settings.LANGUAGE_CODE_FR
        proposition = cls._load_dto(admission)
        poursuite_de_cycle_a_specifier = proposition.formation.type == TrainingType.BACHELOR.name

        return PropositionGestionnaireDTO(
            **dto_to_dict(proposition),
            date_changement_statut=admission.status_updated_at,  # from annotation
            genre_candidat=admission.candidate.gender,
            noma_candidat=admission.student_registration_id or '',  # from annotation
            photo_identite_candidat=admission.candidate.id_photo,
            adresse_email_candidat=admission.candidate.private_email,
            langue_contact_candidat=admission.candidate.language,
            nationalite_candidat=(
                getattr(
                    admission.candidate.country_of_citizenship,
                    'name' if is_french_language else 'name_en',
                )
                if admission.candidate.country_of_citizenship
                else ''
            ),
            nationalite_candidat_fr=(
                admission.candidate.country_of_citizenship.name if admission.candidate.country_of_citizenship else ''
            ),
            nationalite_candidat_en=(
                admission.candidate.country_of_citizenship.name_en if admission.candidate.country_of_citizenship else ''
            ),
            nationalite_ue_candidat=admission.candidate.country_of_citizenship
            and admission.candidate.country_of_citizenship.european_union,
            nationalite_candidat_code_iso=(
                admission.candidate.country_of_citizenship.iso_code
                if admission.candidate.country_of_citizenship
                else ''
            ),
            poursuite_de_cycle_a_specifier=poursuite_de_cycle_a_specifier,
            poursuite_de_cycle=admission.cycle_pursuit if poursuite_de_cycle_a_specifier else '',
            candidat_a_plusieurs_demandes=admission.has_several_admissions_in_progress,  # from annotation
            titre_acces='',  # TODO
            candidat_assimile=admission.accounting
            and admission.accounting.assimilation_situation
            and admission.accounting.assimilation_situation != TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
            fraudeur_ares=False,  # TODO
            non_financable=False,  # TODO,
            est_inscription_tardive=admission.late_enrollment,
            profil_soumis_candidat=(
                ProfilCandidatDTO.from_dict(
                    dict_profile=admission.submitted_profile,
                    nom_pays_nationalite=admission.submitted_profile_country_of_citizenship_name,  # from annotation
                    nom_pays_adresse=admission.submitted_profile_country_name,  # from annotation
                )
                if admission.submitted_profile
                else None
            ),
            type_de_refus=admission.refusal_type,
            motifs_refus=[
                MotifRefusDTO(motif=mark_safe(reason.name), categorie=reason.category.name)
                for reason in admission.refusal_reasons.all()
            ]
            + [
                MotifRefusDTO(motif=reason, categorie=pgettext('admission', 'Other reasons'))
                for reason in admission.other_refusal_reasons
            ],
            autre_formation_choisie_fac=(
                BaseFormationDTO(
                    sigle=admission.other_training_accepted_by_fac.acronym,
                    annee=admission.other_training_accepted_by_fac.academic_year.year,
                    uuid=admission.other_training_accepted_by_fac.uuid,
                    intitule=(
                        admission.other_training_accepted_by_fac.title
                        if get_language() == settings.LANGUAGE_CODE_FR
                        else admission.other_training_accepted_by_fac.title_english
                    ),
                    lieu_enseignement=admission.other_training_accepted_by_fac_teaching_campus,  # From annotation
                )
                if admission.other_training_accepted_by_fac_id
                else None
            ),
            avec_conditions_complementaires=admission.with_additional_approval_conditions,
            conditions_complementaires=[
                ConditionComplementaireApprobationDTO(
                    uuid=condition.uuid,
                    nom_fr=mark_safe(condition.name_fr),
                    nom_en=mark_safe(condition.name_en),
                    libre=False,
                )
                for condition in admission.additional_approval_conditions.all()
            ]
            + [
                ConditionComplementaireApprobationDTO(
                    uuid=condition.uuid,
                    nom_fr=mark_safe(condition.name_fr),
                    nom_en=mark_safe(condition.name_en),
                    libre=True,
                    uuid_experience=str(condition.related_experience_id) if condition.related_experience_id else '',
                )
                for condition in admission.freeadditionalapprovalcondition_set.all()
            ],
            avec_complements_formation=admission.with_prerequisite_courses,
            complements_formation=prerequisite_courses,
            commentaire_complements_formation=admission.prerequisite_courses_fac_comment,
            nombre_annees_prevoir_programme=admission.program_planned_years_number,
            nom_personne_contact_programme_annuel_annuel=admission.annual_program_contact_person_name,
            email_personne_contact_programme_annuel_annuel=admission.annual_program_contact_person_email,
            commentaire_programme_conjoint=admission.join_program_fac_comment,
            condition_acces=admission.admission_requirement,
            millesime_condition_acces=(
                admission.admission_requirement_year.year if admission.admission_requirement_year else None
            ),
            type_equivalence_titre_acces=admission.foreign_access_title_equivalency_type,
            information_a_propos_de_la_restriction=admission.foreign_access_title_equivalency_restriction_about,
            statut_equivalence_titre_acces=admission.foreign_access_title_equivalency_status,
            etat_equivalence_titre_acces=admission.foreign_access_title_equivalency_state,
            date_prise_effet_equivalence_titre_acces=admission.foreign_access_title_equivalency_effective_date,
            besoin_de_derogation=admission.dispensation_needed,
            droits_inscription_montant=admission.tuition_fees_amount,
            droits_inscription_montant_valeur=DROITS_INSCRIPTION_MONTANT_VALEURS.get(admission.tuition_fees_amount),
            droits_inscription_montant_autre=admission.tuition_fees_amount_other,
            dispense_ou_droits_majores=admission.tuition_fees_dispensation,
            tarif_particulier=admission.particular_cost,
            refacturation_ou_tiers_payant=admission.rebilling_or_third_party_payer,
            annee_de_premiere_inscription_et_statut=admission.first_year_inscription_and_status,
            est_mobilite=admission.is_mobility,
            nombre_de_mois_de_mobilite=admission.mobility_months_amount,
            doit_se_presenter_en_sic=admission.must_report_to_sic,
            communication_au_candidat=admission.communication_to_the_candidate,
        )

    @classmethod
    def get_dto_for_gestionnaire(
        cls,
        entity_id: 'PropositionIdentity',
        unites_enseignement_translator: 'IUnitesEnseignementTranslator',
    ) -> 'PropositionGestionnaireDTO':
        try:
            admission = (
                GeneralEducationAdmissionProxy.objects.for_manager_dto()
                .annotate_several_admissions_in_progress()
                .annotate_submitted_profile_countries_names()
                .annotate(
                    status_updated_at=Subquery(
                        HistoryEntry.objects.filter(
                            object_uuid=OuterRef('uuid'),
                            tags__contains=['proposition', 'status-changed'],
                        ).values('created')[:1]
                    ),
                )
                .select_related(
                    'accounting',
                    'other_training_accepted_by_fac__academic_year',
                    'admission_requirement_year',
                )
                .prefetch_related(
                    'additional_approval_conditions',
                    'freeadditionalapprovalcondition_set',
                    Prefetch(
                        'refusal_reasons',
                        queryset=RefusalReason.objects.select_related('category').order_by('category__order', 'order'),
                    ),
                )
                .get(uuid=entity_id.uuid)
            )

            prerequisite_courses = unites_enseignement_translator.search(
                code_annee_valeurs=admission.prerequisite_courses.all().values_list('acronym', 'academic_year__year'),
            )

            return cls._load_dto_for_gestionnaire(admission, prerequisite_courses)
        except GeneralEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException
