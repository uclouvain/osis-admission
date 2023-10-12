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
from enum import Enum
from typing import List, Optional, Union

import attrs
from django.conf import settings
from django.db.models import OuterRef, Subquery
from django.utils.translation import get_language, gettext
from osis_history.models import HistoryEntry

from admission.auth.roles.candidate import Candidate
from admission.contrib.models import Accounting, GeneralEducationAdmissionProxy, Scholarship, DiplomaticPost
from admission.contrib.models.general_education import GeneralEducationAdmission
from admission.ddd import BE_ISO_CODE
from admission.ddd.admission.domain.builder.formation_identity import FormationIdentityBuilder
from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.model.bourse import BourseIdentity
from admission.ddd.admission.domain.model.complement_formation import ComplementFormationIdentity
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
)
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.domain.model.poste_diplomatique import PosteDiplomatiqueIdentity
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import IUnitesEnseignementTranslator
from admission.ddd.admission.dtos.formation import FormationDTO, BaseFormationDTO
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    StatutChecklist,
    StatutsChecklistGenerale,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from admission.ddd.admission.formation_generale.dtos.motif_refus import MotifRefusDTO
from admission.ddd.admission.formation_generale.dtos.proposition import PropositionGestionnaireDTO
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.infrastructure.admission.domain.service.bourse import BourseTranslator
from admission.infrastructure.admission.domain.service.poste_diplomatique import PosteDiplomatiqueTranslator
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.infrastructure.admission.formation_generale.repository._comptabilite import get_accounting_from_admission
from admission.infrastructure.admission.repository.proposition import GlobalPropositionRepository
from admission.infrastructure.utils import dto_to_dict
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from base.models.student import Student
from ddd.logic.learning_unit.dtos import LearningUnitPartimDTO, PartimSearchDTO
from ddd.logic.learning_unit.dtos import LearningUnitSearchDTO
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from osis_common.ddd.interface import ApplicationService
from osis_profile.models.enums.curriculum import Result


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
                    'prerequisite_courses',
                )
                .select_related(
                    'other_training_accepted_by_fac__academic_year',
                    'fac_refusal_reason',
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
    def save(cls, entity: 'Proposition') -> None:
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
                'determined_pool': entity.pot_calcule and entity.pot_calcule.name,
                'reference': entity.reference,
                'type_demande': entity.type_demande.name,
                'submitted_at': entity.soumise_le,
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
                'fac_approval_certificate': entity.certificat_approbation_fac,
                'fac_refusal_certificate': entity.certificat_refus_fac,
                'fac_refusal_reason_id': entity.motif_refus_fac and entity.motif_refus_fac.uuid,
                'other_fac_refusal_reason': entity.autre_motif_refus_fac,
                'other_training_accepted_by_fac': other_training,
                'with_additional_approval_conditions': entity.avec_conditions_complementaires,
                'free_additional_approval_conditions': entity.conditions_complementaires_libres,
                'with_prerequisite_courses': entity.avec_complements_formation,
                'prerequisite_courses_fac_comment': entity.commentaire_complements_formation,
                'program_planned_years_number': entity.nombre_annees_prevoir_programme,
                'annual_program_contact_person_name': entity.nom_personne_contact_programme_annuel_annuel,
                'annual_program_contact_person_email': entity.email_personne_contact_programme_annuel_annuel,
                'join_program_fac_comment': entity.commentaire_programme_conjoint,
                'additional_documents': entity.documents_additionnels,
                'diplomatic_post_id': entity.poste_diplomatique.code if entity.poste_diplomatique else None,
            },
        )

        Candidate.objects.get_or_create(person=candidate)
        cls._sauvegarder_comptabilite(admission, entity)

        admission.additional_approval_conditions.set([c.uuid for c in entity.conditions_complementaires_existantes])
        admission.prerequisite_courses.set([training.uuid for training in entity.complements_formation])

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
                'stateless_person_proof': entity.comptabilite.preuve_statut_apatride,
                'a_b_card': entity.comptabilite.carte_a_b,
                'subsidiary_protection_decision': entity.comptabilite.decision_protection_subsidiaire,
                'temporary_protection_decision': entity.comptabilite.decision_protection_temporaire,
                'a_card': entity.comptabilite.carte_a,
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
            return cls._load_dto(GeneralEducationAdmissionProxy.objects.for_dto().get(uuid=entity_id.uuid))
        except GeneralEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def _load(cls, admission: 'GeneralEducationAdmission') -> 'Proposition':
        checklist_initiale = admission.checklist.get('initial')
        checklist_actuelle = admission.checklist.get('current')
        return Proposition(
            entity_id=PropositionIdentityBuilder().build_from_uuid(admission.uuid),
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
            comptabilite=get_accounting_from_admission(admission=admission),
            elements_confirmation=admission.confirmation_elements,
            est_inscription_tardive=admission.late_enrollment,
            profil_soumis_candidat=ProfilCandidat.from_dict(admission.submitted_profile)
            if admission.submitted_profile
            else None,
            documents_demandes=admission.requested_documents,
            checklist_initiale=checklist_initiale and StatutsChecklistGenerale.from_dict(checklist_initiale),
            checklist_actuelle=checklist_actuelle and StatutsChecklistGenerale.from_dict(checklist_actuelle),
            motif_refus_fac=MotifRefusIdentity(uuid=admission.fac_refusal_reason.uuid)
            if admission.fac_refusal_reason
            else None,
            autre_motif_refus_fac=admission.other_fac_refusal_reason,
            certificat_refus_fac=admission.fac_refusal_certificate,
            certificat_approbation_fac=admission.fac_approval_certificate,
            autre_formation_choisie_fac_id=FormationIdentityBuilder.build(
                sigle=admission.other_training_accepted_by_fac.acronym,
                annee=admission.other_training_accepted_by_fac.academic_year.year,
            )
            if admission.other_training_accepted_by_fac_id
            else None,
            avec_conditions_complementaires=admission.with_additional_approval_conditions,
            conditions_complementaires_existantes=[
                ConditionComplementaireApprobationIdentity(uuid=condition.uuid)
                for condition in admission.additional_approval_conditions.all()
            ],
            conditions_complementaires_libres=admission.free_additional_approval_conditions,
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
            poste_diplomatique=PosteDiplomatiqueIdentity(code=admission.diplomatic_post.code)
            if admission.diplomatic_post
            else None,
        )

    @classmethod
    def _load_dto(cls, admission: GeneralEducationAdmission) -> 'PropositionDTO':
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
                intitule=admission.training.title
                if get_language() == settings.LANGUAGE_CODE_FR
                else admission.training.title_english,
                campus=admission.teaching_campus or '',  # from annotation
                type=admission.training.education_group_type.name,
                code_domaine=admission.training.main_domain.code if admission.training.main_domain else '',
                campus_inscription=admission.training.enrollment_campus.name,
                sigle_entite_gestion=admission.training_management_faculty
                or admission.sigle_entite_gestion,  # from annotation
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
            est_bachelier_belge=admission.is_belgian_bachelor,
            est_non_resident_au_sens_decret=admission.is_non_resident,
            elements_confirmation=admission.confirmation_elements,
            est_modification_inscription_externe=admission.is_external_modification,
            formulaire_modification_inscription=admission.registration_change_form,
            est_reorientation_inscription_externe=admission.is_external_reorientation,
            attestation_inscription_reguliere=admission.regular_registration_proof,
            pdf_recapitulatif=admission.pdf_recap,
            documents_demandes=admission.requested_documents,
            documents_libres_fac_uclouvain=admission.uclouvain_fac_documents,
            documents_libres_sic_uclouvain=admission.uclouvain_sic_documents,
            certificat_refus_fac=admission.fac_refusal_certificate,
            certificat_approbation_fac=admission.fac_approval_certificate,
            documents_additionnels=admission.additional_documents,
            poste_diplomatique=PosteDiplomatiqueTranslator.build_dto(admission.diplomatic_post)
            if admission.diplomatic_post
            else None,
        )

    @classmethod
    def _load_dto_for_gestionnaire(
        cls,
        admission: GeneralEducationAdmission,
        prerequisite_courses: List[Union['PartimSearchDTO', 'LearningUnitSearchDTO']],
    ) -> 'PropositionGestionnaireDTO':
        is_french_language = get_language() == settings.LANGUAGE_CODE_FR
        proposition = cls._load_dto(admission)
        annee_courante = (
            GetCurrentAcademicYear()
            .get_starting_academic_year(
                datetime.date.today(),
                AcademicYearRepository,
            )
            .year
        )
        curriculum = ProfilCandidatTranslator.get_curriculum(
            matricule=proposition.matricule_candidat,
            annee_courante=annee_courante,
        )
        candidat_a_reussi_experience_academique_belge = any(
            annee.resultat == Result.SUCCESS.name or annee.resultat == Result.SUCCESS_WITH_RESIDUAL_CREDITS.name
            for experience in curriculum.experiences_academiques
            for annee in experience.annees
            if experience.pays == BE_ISO_CODE
        )
        poursuite_de_cycle_a_specifier = (
            proposition.formation.type == TrainingType.BACHELOR.name and candidat_a_reussi_experience_academique_belge
        )
        additional_condition_title_field = 'name_fr' if is_french_language else 'name_en'
        additional_training_title_field = 'full_title' if is_french_language else 'full_title_en'

        return PropositionGestionnaireDTO(
            **dto_to_dict(proposition),
            type=admission.type_demande,
            date_changement_statut=admission.status_updated_at,  # from annotation
            genre_candidat=admission.candidate.gender,
            noma_candidat=admission.student_registration_id or '',  # from annotation
            photo_identite_candidat=admission.candidate.id_photo,
            adresse_email_candidat=admission.candidate.private_email,
            langue_contact_candidat=admission.candidate.language,
            nationalite_candidat=getattr(
                admission.candidate.country_of_citizenship,
                'name' if is_french_language else 'name_en',
            )
            if admission.candidate.country_of_citizenship
            else '',
            nationalite_ue_candidat=admission.candidate.country_of_citizenship
            and admission.candidate.country_of_citizenship.european_union,
            poursuite_de_cycle_a_specifier=poursuite_de_cycle_a_specifier,
            poursuite_de_cycle=admission.cycle_pursuit if poursuite_de_cycle_a_specifier else '',
            candidat_a_plusieurs_demandes=admission.has_several_admissions_in_progress,  # from annotation
            titre_access='',  # TODO
            candidat_assimile=admission.accounting
            and admission.accounting.assimilation_situation
            and admission.accounting.assimilation_situation != TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
            fraudeur_ares=False,  # TODO
            non_financable=False,  # TODO,
            est_inscription_tardive=admission.late_enrollment,
            profil_soumis_candidat=ProfilCandidatDTO.from_dict(
                dict_profile=admission.submitted_profile,
                nom_pays_nationalite=admission.submitted_profile_country_of_citizenship_name,  # from annotation
                nom_pays_adresse=admission.submitted_profile_country_name,  # from annotation
            )
            if admission.submitted_profile
            else None,
            motif_refus_fac=(
                MotifRefusDTO(
                    motif=getattr(
                        admission.fac_refusal_reason,
                        'name_fr' if is_french_language else 'name_en',
                    ),
                    categorie=getattr(
                        admission.fac_refusal_reason.category,
                        'name_fr' if is_french_language else 'name_en',
                    ),
                )
                if admission.fac_refusal_reason
                else MotifRefusDTO(
                    motif=admission.other_fac_refusal_reason,
                    categorie=gettext('Other'),
                )
                if admission.other_fac_refusal_reason
                else None
            ),
            autre_formation_choisie_fac=BaseFormationDTO(
                sigle=admission.other_training_accepted_by_fac.acronym,
                annee=admission.other_training_accepted_by_fac.academic_year.year,
                uuid=admission.other_training_accepted_by_fac.uuid,
                intitule=admission.other_training_accepted_by_fac.title
                if get_language() == settings.LANGUAGE_CODE_FR
                else admission.other_training_accepted_by_fac.title_english,
                lieu_enseignement=admission.other_training_accepted_by_fac_teaching_campus,  # From annotation
            )
            if admission.other_training_accepted_by_fac_id
            else None,
            avec_conditions_complementaires=admission.with_additional_approval_conditions,
            conditions_complementaires=[
                getattr(condition, additional_condition_title_field)
                for condition in admission.additional_approval_conditions.all()
            ]
            + admission.free_additional_approval_conditions,
            avec_complements_formation=admission.with_prerequisite_courses,
            complements_formation=[
                LearningUnitPartimDTO(
                    code=learning_unit_partim.code,
                    full_title=getattr(learning_unit_partim, additional_training_title_field),
                )
                for learning_unit_partim in prerequisite_courses
            ],
            commentaire_complements_formation=admission.prerequisite_courses_fac_comment,
            nombre_annees_prevoir_programme=admission.program_planned_years_number,
            nom_personne_contact_programme_annuel_annuel=admission.annual_program_contact_person_name,
            email_personne_contact_programme_annuel_annuel=admission.annual_program_contact_person_email,
            commentaire_programme_conjoint=admission.join_program_fac_comment,
            candidat_a_reussi_experience_academique_belge=candidat_a_reussi_experience_academique_belge,
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
                    student_registration_id=Subquery(
                        Student.objects.filter(person_id=OuterRef('candidate_id'),).values(
                            'registration_id'
                        )[:1],
                    ),
                )
                .select_related(
                    'accounting',
                    'other_training_accepted_by_fac__academic_year',
                    'fac_refusal_reason',
                )
                .prefetch_related(
                    'prerequisite_courses__academic_year',
                    'additional_approval_conditions',
                )
                .get(uuid=entity_id.uuid)
            )

            prerequisite_courses = unites_enseignement_translator.search(
                code_annee_valeurs=admission.prerequisite_courses.all().values_list('acronym', 'academic_year__year'),
            )

            return cls._load_dto_for_gestionnaire(admission, prerequisite_courses)
        except GeneralEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException
