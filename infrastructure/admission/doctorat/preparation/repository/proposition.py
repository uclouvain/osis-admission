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
from datetime import date
from enum import Enum
from typing import List, Optional, Union

import attrs
from django.conf import settings
from django.db.models import OuterRef, Subquery
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, pgettext

from admission.auth.roles.candidate import Candidate
from admission.contrib.models import Accounting, DoctorateAdmission
from admission.contrib.models.doctorate import PropositionProxy
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import (
    DetailProjet,
)
from admission.ddd.admission.doctorat.preparation.domain.model._experience_precedente_recherche import (
    ExperiencePrecedenteRecherche,
)
from admission.ddd.admission.doctorat.preparation.domain.model._financement import (
    Financement,
)
from admission.ddd.admission.doctorat.preparation.domain.model._institut import (
    InstitutIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    BourseRecherche,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixSousDomaineSciences,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    DerogationFinancement,
    BesoinDeDerogation,
    DROITS_INSCRIPTION_MONTANT_VALEURS,
    DroitsInscriptionMontant,
    DispenseOuDroitsMajores,
    MobiliteNombreDeMois,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    StatutsChecklistDoctorale,
    StatutChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.ddd.admission.doctorat.preparation.dtos import (
    DoctoratDTO,
    PropositionDTO,
    CotutelleDTO,
)
from admission.ddd.admission.doctorat.preparation.dtos import PropositionGestionnaireDTO
from admission.ddd.admission.doctorat.preparation.dtos.motif_refus import MotifRefusDTO
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.model.bourse import BourseIdentity
from admission.ddd.admission.domain.model.complement_formation import ComplementFormationIdentity
from admission.ddd.admission.domain.model.enums.equivalence import (
    TypeEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    EtatEquivalenceTitreAcces,
)
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import IUnitesEnseignementTranslator
from admission.ddd.admission.dtos.campus import CampusDTO
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.infrastructure.admission.doctorat.preparation.repository._comptabilite import (
    get_accounting_from_admission,
)
from admission.infrastructure.admission.domain.service.bourse import BourseTranslator
from admission.infrastructure.admission.repository.proposition import GlobalPropositionRepository
from admission.infrastructure.utils import dto_to_dict
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.person import Person
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.financabilite.domain.model.enums.situation import SituationFinancabilite
from ddd.logic.learning_unit.dtos import LearningUnitSearchDTO
from ddd.logic.learning_unit.dtos import PartimSearchDTO
from epc.models.enums.condition_acces import ConditionAcces
from osis_common.ddd.interface import ApplicationService
from reference.models.language import Language


def _instantiate_admission(admission: 'DoctorateAdmission') -> 'Proposition':
    commission_proximite = None
    if admission.proximity_commission in ChoixCommissionProximiteCDEouCLSM.get_names():
        commission_proximite = ChoixCommissionProximiteCDEouCLSM[admission.proximity_commission]
    elif admission.proximity_commission in ChoixCommissionProximiteCDSS.get_names():
        commission_proximite = ChoixCommissionProximiteCDSS[admission.proximity_commission]
    elif admission.proximity_commission in ChoixSousDomaineSciences.get_names():
        commission_proximite = ChoixSousDomaineSciences[admission.proximity_commission]

    checklist_initiale = admission.checklist.get('initial')
    checklist_actuelle = admission.checklist.get('current')

    return Proposition(
        entity_id=PropositionIdentityBuilder().build_from_uuid(admission.uuid),
        commission_proximite=commission_proximite,
        type_admission=ChoixTypeAdmission[admission.type],
        formation_id=FormationIdentity(admission.doctorate.acronym, admission.doctorate.academic_year.year),
        annee_calculee=admission.determined_academic_year and admission.determined_academic_year.year,
        type_demande=TypeDemande[admission.type_demande],
        pot_calcule=admission.determined_pool and AcademicCalendarTypes[admission.determined_pool],
        matricule_candidat=admission.candidate.global_id,
        reference=admission.reference,
        projet=DetailProjet(
            titre=admission.project_title,
            resume=admission.project_abstract,
            documents=admission.project_document,
            langue_redaction_these=admission.thesis_language.code if admission.thesis_language else '',
            institut_these=InstitutIdentity(admission.thesis_institute.uuid) if admission.thesis_institute_id else None,
            lieu_these=admission.thesis_location,
            deja_commence=admission.phd_alread_started,
            deja_commence_institution=admission.phd_alread_started_institute,
            date_debut=admission.work_start_date,
            graphe_gantt=admission.gantt_graph,
            proposition_programme_doctoral=admission.program_proposition,
            projet_formation_complementaire=admission.additional_training_project,
            lettres_recommandation=admission.recommendation_letters,
        ),
        justification=admission.comment,
        statut=ChoixStatutPropositionDoctorale[admission.status],
        financement=Financement(
            type=ChoixTypeFinancement[admission.financing_type] if admission.financing_type else None,
            type_contrat_travail=admission.financing_work_contract,
            eft=admission.financing_eft,
            bourse_recherche=BourseIdentity(uuid=str(admission.international_scholarship_id))
            if admission.international_scholarship_id
            else None,
            autre_bourse_recherche=admission.other_international_scholarship,
            bourse_date_debut=admission.scholarship_start_date,
            bourse_date_fin=admission.scholarship_end_date,
            bourse_preuve=admission.scholarship_proof,
            duree_prevue=admission.planned_duration,
            temps_consacre=admission.dedicated_time,
            est_lie_fnrs_fria_fresh_csc=admission.is_fnrs_fria_fresh_csc_linked,
            commentaire=admission.financing_comment,
        ),
        experience_precedente_recherche=ExperiencePrecedenteRecherche(
            doctorat_deja_realise=ChoixDoctoratDejaRealise[admission.phd_already_done],
            institution=admission.phd_already_done_institution,
            domaine_these=admission.phd_already_done_thesis_domain,
            date_soutenance=admission.phd_already_done_defense_date,
            raison_non_soutenue=admission.phd_already_done_no_defense_reason,
        ),
        creee_le=admission.created_at,
        modifiee_le=admission.modified_at,
        soumise_le=admission.submitted_at,
        comptabilite=get_accounting_from_admission(admission=admission),
        reponses_questions_specifiques=admission.specific_question_answers,
        curriculum=admission.curriculum,
        elements_confirmation=admission.confirmation_elements,
        fiche_archive_signatures_envoyees=admission.archived_record_signatures_sent,
        auteur_derniere_modification=admission.last_update_author.global_id if admission.last_update_author else '',
        documents_demandes=admission.requested_documents,
        profil_soumis_candidat=ProfilCandidat.from_dict(admission.submitted_profile)
        if admission.submitted_profile
        else None,
        checklist_initiale=checklist_initiale and StatutsChecklistDoctorale.from_dict(checklist_initiale),
        checklist_actuelle=checklist_actuelle and StatutsChecklistDoctorale.from_dict(checklist_actuelle),
        motifs_refus=[MotifRefusIdentity(uuid=motif.uuid) for motif in admission.refusal_reasons.all()],
        autres_motifs_refus=admission.other_refusal_reasons,
        financabilite_regle_calcule=EtatFinancabilite[admission.financability_computed_rule]
        if admission.financability_computed_rule
        else None,
        financabilite_regle_calcule_situation=SituationFinancabilite[admission.financability_computed_rule_situation]
        if admission.financability_computed_rule_situation
        else None,
        financabilite_regle_calcule_le=admission.financability_computed_rule_on,
        financabilite_regle=SituationFinancabilite[admission.financability_rule]
        if admission.financability_rule
        else None,
        financabilite_regle_etabli_par=admission.financability_rule_established_by.uuid
        if admission.financability_rule_established_by
        else None,
        financabilite_regle_etabli_le=admission.financability_rule_established_on,
        financabilite_derogation_statut=DerogationFinancement[admission.financability_dispensation_status]
        if admission.financability_dispensation_status
        else None,
        financabilite_derogation_premiere_notification_le=admission.financability_dispensation_first_notification_on,
        financabilite_derogation_premiere_notification_par=(
            admission.financability_dispensation_first_notification_by.global_id
            if admission.financability_dispensation_first_notification_by
            else None
        ),
        financabilite_derogation_derniere_notification_le=admission.financability_dispensation_last_notification_on,
        financabilite_derogation_derniere_notification_par=(
            admission.financability_dispensation_last_notification_by.global_id
            if admission.financability_dispensation_last_notification_by
            else None
        ),
        certificat_approbation_fac=admission.fac_approval_certificate,
        certificat_approbation_sic=admission.sic_approval_certificate,
        certificat_approbation_sic_annexe=admission.sic_annexe_approval_certificate,
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
        condition_acces=ConditionAcces[admission.admission_requirement] if admission.admission_requirement else None,
        millesime_condition_acces=admission.admission_requirement_year and admission.admission_requirement_year.year,
        information_a_propos_de_la_restriction=admission.foreign_access_title_equivalency_restriction_about,
        type_equivalence_titre_acces=TypeEquivalenceTitreAcces[admission.foreign_access_title_equivalency_type]
        if admission.foreign_access_title_equivalency_type
        else None,
        statut_equivalence_titre_acces=StatutEquivalenceTitreAcces[admission.foreign_access_title_equivalency_status]
        if admission.foreign_access_title_equivalency_status
        else None,
        etat_equivalence_titre_acces=EtatEquivalenceTitreAcces[admission.foreign_access_title_equivalency_state]
        if admission.foreign_access_title_equivalency_state
        else None,
        date_prise_effet_equivalence_titre_acces=admission.foreign_access_title_equivalency_effective_date,
        besoin_de_derogation=BesoinDeDerogation[admission.dispensation_needed]
        if admission.dispensation_needed
        else None,
        droits_inscription_montant=DroitsInscriptionMontant[admission.tuition_fees_amount]
        if admission.tuition_fees_amount
        else None,
        droits_inscription_montant_autre=admission.tuition_fees_amount_other,
        dispense_ou_droits_majores=DispenseOuDroitsMajores[admission.tuition_fees_dispensation]
        if admission.tuition_fees_dispensation
        else None,
        est_mobilite=admission.is_mobility,
        nombre_de_mois_de_mobilite=MobiliteNombreDeMois[admission.mobility_months_amount]
        if admission.mobility_months_amount
        else None,
        doit_se_presenter_en_sic=admission.must_report_to_sic,
        communication_au_candidat=admission.communication_to_the_candidate,
        doit_fournir_visa_etudes=admission.must_provide_student_visa_d,
        visa_etudes_d=admission.student_visa_d,
        certificat_autorisation_signe=admission.signed_enrollment_authorization,
    )


def load_admissions(matricule: Optional[str] = None, ids: Optional[List[str]] = None) -> List['Proposition']:
    qs = []
    if matricule is not None:
        qs = PropositionProxy.objects.for_domain_model().filter(candidate__global_id=matricule)
    elif ids is not None:  # pragma: no branch
        qs = PropositionProxy.objects.for_domain_model().filter(uuid__in=ids)

    return [_instantiate_admission(a) for a in qs]


class PropositionRepository(GlobalPropositionRepository, IPropositionRepository):
    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        try:
            return _instantiate_admission(PropositionProxy.objects.for_domain_model().get(uuid=entity_id.uuid))
        except DoctorateAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def search(
        cls,
        entity_ids: Optional[List['PropositionIdentity']] = None,
        matricule_candidat: str = None,
        **kwargs,
    ) -> List['Proposition']:
        if matricule_candidat is not None:
            return load_admissions(matricule=matricule_candidat)
        if entity_ids is not None:
            return load_admissions(ids=[e.uuid for e in entity_ids])
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'PropositionIdentity', **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def save(cls, entity: 'Proposition') -> None:
        doctorate = EducationGroupYear.objects.get(
            acronym=entity.sigle_formation,
            academic_year__year=entity.annee,
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
                    ]
                    if matricule
                ]
            )
        }

        candidate = persons[entity.matricule_candidat]

        last_update_author = (
            persons[entity.auteur_derniere_modification] if entity.auteur_derniere_modification in persons else None
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

        financabilite_regle_etabli_par_person = None
        if entity.financabilite_regle_etabli_par:
            financabilite_regle_etabli_par_person = Person.objects.filter(
                uuid=entity.financabilite_regle_etabli_par,
            ).first()

        years = [year for year in [entity.annee_calculee, entity.millesime_condition_acces] if year]
        academic_years = {}

        if years:
            academic_years = {year.year: year for year in AcademicYear.objects.filter(year__in=years)}

        admission, _ = DoctorateAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'reference': entity.reference,
                'type': entity.type_admission.name,
                'status': entity.statut.name,
                'comment': entity.justification,
                'candidate': candidate,
                'submitted_at': entity.soumise_le,
                'proximity_commission': entity.commission_proximite and entity.commission_proximite.name or '',
                'doctorate': doctorate,
                'determined_academic_year': academic_years.get(entity.annee_calculee),
                'type_demande': entity.type_demande.name,
                'determined_pool': entity.pot_calcule and entity.pot_calcule.name,
                'financing_type': entity.financement.type and entity.financement.type.name or '',
                'financing_work_contract': entity.financement.type_contrat_travail,
                'financing_eft': entity.financement.eft,
                'international_scholarship_id': entity.financement.bourse_recherche
                and entity.financement.bourse_recherche.uuid,
                'other_international_scholarship': entity.financement.autre_bourse_recherche,
                'scholarship_start_date': entity.financement.bourse_date_debut,
                'scholarship_end_date': entity.financement.bourse_date_fin,
                'scholarship_proof': entity.financement.bourse_preuve,
                'planned_duration': entity.financement.duree_prevue,
                'dedicated_time': entity.financement.temps_consacre,
                'is_fnrs_fria_fresh_csc_linked': entity.financement.est_lie_fnrs_fria_fresh_csc,
                'financing_comment': entity.financement.commentaire,
                'project_title': entity.projet.titre,
                'project_abstract': entity.projet.resume,
                'thesis_language': (
                    Language.objects.get(code=entity.projet.langue_redaction_these)
                    if entity.projet.langue_redaction_these
                    else None
                ),
                'thesis_institute': (
                    EntityVersion.objects.get(uuid=entity.projet.institut_these.uuid)
                    if entity.projet.institut_these
                    else None
                ),
                'thesis_location': entity.projet.lieu_these,
                'phd_alread_started': entity.projet.deja_commence,
                'phd_alread_started_institute': entity.projet.deja_commence_institution,
                'work_start_date': entity.projet.date_debut,
                'project_document': entity.projet.documents,
                'gantt_graph': entity.projet.graphe_gantt,
                'program_proposition': entity.projet.proposition_programme_doctoral,
                'additional_training_project': entity.projet.projet_formation_complementaire,
                'recommendation_letters': entity.projet.lettres_recommandation,
                'phd_already_done': entity.experience_precedente_recherche.doctorat_deja_realise.name,
                'phd_already_done_institution': entity.experience_precedente_recherche.institution,
                'phd_already_done_thesis_domain': entity.experience_precedente_recherche.domaine_these,
                'phd_already_done_defense_date': entity.experience_precedente_recherche.date_soutenance,
                'phd_already_done_no_defense_reason': entity.experience_precedente_recherche.raison_non_soutenue,
                'archived_record_signatures_sent': entity.fiche_archive_signatures_envoyees,
                'specific_question_answers': entity.reponses_questions_specifiques,
                'curriculum': entity.curriculum,
                'confirmation_elements': entity.elements_confirmation,
                'submitted_profile': entity.profil_soumis_candidat.to_dict() if entity.profil_soumis_candidat else {},
                'last_update_author': last_update_author,
                'checklist': {
                    'initial': entity.checklist_initiale
                    and attrs.asdict(entity.checklist_initiale, value_serializer=cls._serialize)
                    or {},
                    'current': entity.checklist_actuelle
                    and attrs.asdict(entity.checklist_actuelle, value_serializer=cls._serialize)
                    or {},
                },
                'financability_computed_rule': entity.financabilite_regle_calcule.name
                if entity.financabilite_regle_calcule
                else '',
                'financability_computed_rule_situation': entity.financabilite_regle_calcule_situation.name
                if entity.financabilite_regle_calcule_situation
                else '',
                'financability_computed_rule_on': entity.financabilite_regle_calcule_le,
                'financability_rule': entity.financabilite_regle.name if entity.financabilite_regle else '',
                'financability_rule_established_by': financabilite_regle_etabli_par_person,
                'financability_rule_established_on': entity.financabilite_regle_etabli_le,
                'financability_dispensation_status': entity.financabilite_derogation_statut.name
                if entity.financabilite_derogation_statut
                else '',
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
                'fac_approval_certificate': entity.certificat_approbation_fac,
                'sic_approval_certificate': entity.certificat_approbation_sic,
                'sic_annexe_approval_certificate': entity.certificat_approbation_sic_annexe,
                'other_refusal_reasons': entity.autres_motifs_refus,
                'with_prerequisite_courses': entity.avec_complements_formation,
                'prerequisite_courses_fac_comment': entity.commentaire_complements_formation,
                'program_planned_years_number': entity.nombre_annees_prevoir_programme,
                'annual_program_contact_person_name': entity.nom_personne_contact_programme_annuel_annuel,
                'annual_program_contact_person_email': entity.email_personne_contact_programme_annuel_annuel,
                'join_program_fac_comment': entity.commentaire_programme_conjoint,
                'admission_requirement': entity.condition_acces.name if entity.condition_acces else '',
                'admission_requirement_year': academic_years.get(entity.millesime_condition_acces),
                'foreign_access_title_equivalency_type': entity.type_equivalence_titre_acces.name
                if entity.type_equivalence_titre_acces
                else '',
                'foreign_access_title_equivalency_restriction_about': entity.information_a_propos_de_la_restriction,
                'foreign_access_title_equivalency_status': entity.statut_equivalence_titre_acces.name
                if entity.statut_equivalence_titre_acces
                else '',
                'foreign_access_title_equivalency_state': entity.etat_equivalence_titre_acces.name
                if entity.etat_equivalence_titre_acces
                else '',
                'foreign_access_title_equivalency_effective_date': entity.date_prise_effet_equivalence_titre_acces,
                'dispensation_needed': entity.besoin_de_derogation.name if entity.besoin_de_derogation else '',
                'tuition_fees_amount': entity.droits_inscription_montant.name
                if entity.droits_inscription_montant
                else '',
                'tuition_fees_amount_other': entity.droits_inscription_montant_autre,
                'tuition_fees_dispensation': entity.dispense_ou_droits_majores.name
                if entity.dispense_ou_droits_majores
                else '',
                'is_mobility': entity.est_mobilite,
                'mobility_months_amount': entity.nombre_de_mois_de_mobilite.name
                if entity.nombre_de_mois_de_mobilite
                else '',
                'must_report_to_sic': entity.doit_se_presenter_en_sic,
                'communication_to_the_candidate': entity.communication_au_candidat,
                'must_provide_student_visa_d': entity.doit_fournir_visa_etudes,
                'student_visa_d': entity.visa_etudes_d,
                'signed_enrollment_authorization': entity.certificat_autorisation_signe,
            },
        )
        Candidate.objects.get_or_create(person=candidate)

        cls._sauvegarder_comptabilite(admission, entity)

        admission.prerequisite_courses.set([training.uuid for training in entity.complements_formation])
        admission.refusal_reasons.set([motif.uuid for motif in entity.motifs_refus])

    @classmethod
    def _serialize(cls, inst, field, value):
        if isinstance(value, StatutChecklist):
            return attrs.asdict(value, value_serializer=cls._serialize)

        if isinstance(value, Enum):
            return value.name

        return value

    @classmethod
    def _sauvegarder_comptabilite(cls, admission: DoctorateAdmission, entity: Proposition):
        unemployment_benefit_pension_proof = entity.comptabilite.preuve_allocations_chomage_pension_indemnite
        parent_annex_25_26 = entity.comptabilite.annexe_25_26_refugies_apatrides_decision_protection_parent
        Accounting.objects.update_or_create(
            admission=admission,
            defaults={
                'institute_absence_debts_certificate': entity.comptabilite.attestation_absence_dette_etablissement,
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
    def search_dto(
        cls,
        numero: Optional[int] = None,
        matricule_candidat: Optional[str] = '',
        etat: Optional[str] = '',
        nationalite: Optional[str] = '',
        type: Optional[str] = '',
        cdds: Optional[List[str]] = None,
        commission_proximite: Optional[str] = '',
        annee_academique: Optional[str] = None,
        sigles_formations: Optional[List[str]] = None,
        financement: Optional[str] = '',
        type_contrat_travail: Optional[str] = '',
        bourse_recherche: Optional[str] = '',
        matricule_promoteur: Optional[str] = '',
        cotutelle: Optional[bool] = None,
        entity_ids: Optional[List['PropositionIdentity']] = None,
    ) -> List['PropositionDTO']:
        qs = PropositionProxy.objects.for_dto().all()
        if numero is not None:
            qs = qs.filter(reference=numero)
        if matricule_candidat:
            qs = qs.filter(candidate__global_id=matricule_candidat)
        if etat:  # code enum
            qs = qs.filter(status=etat)
        if nationalite:  # code pays
            qs = qs.filter(candidate__country_of_citizenship__iso_code=nationalite)
        if type:
            qs = qs.filter(type=type)
        if commission_proximite:
            qs = qs.filter(proximity_commission=commission_proximite)
        if annee_academique:
            qs = qs.filter(training__academic_year__year=annee_academique)
        if sigles_formations:
            qs = qs.filter(training__acronym__in=sigles_formations)
        if financement:
            qs = qs.filter(financing_type=financement)
        if type_contrat_travail:
            if type_contrat_travail == ChoixTypeContratTravail.OTHER.name:
                qs = qs.exclude(financing_work_contract__in=ChoixTypeContratTravail.get_names())
            else:
                qs = qs.filter(financing_work_contract=type_contrat_travail)
        if bourse_recherche:
            if bourse_recherche == BourseRecherche.OTHER.name:
                qs = qs.filter(international_scholarship_id__isnull=True)
            else:
                qs = qs.filter(international_scholarship_id=bourse_recherche)
        if matricule_promoteur:
            qs = qs.filter(supervision_group__actors__person__global_id=matricule_promoteur)
        if cotutelle is not None:
            qs = qs.filter(cotutelle=cotutelle)
        if cdds:
            qs = qs.alias(
                cdd_acronym=Subquery(
                    EntityVersion.objects.current(date.today())
                    .filter(entity_id=OuterRef('training__management_entity_id'))
                    .values('acronym')[:1]
                )
            ).filter(cdd_acronym__in=cdds)

        if entity_ids is not None:
            qs = qs.filter(uuid__in=[entity_id.uuid for entity_id in entity_ids])

        return [cls._load_dto(admission) for admission in qs]

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(PropositionProxy.objects.for_dto().get(uuid=entity_id.uuid))

    @classmethod
    def _load_dto(cls, admission: DoctorateAdmission) -> 'PropositionDTO':
        return PropositionDTO(
            uuid=admission.uuid,
            reference=admission.formatted_reference,  # from annotation
            type_admission=admission.type,
            doctorat=DoctoratDTO(
                sigle=admission.doctorate.acronym,
                code=admission.doctorate.partial_acronym,
                annee=admission.doctorate.academic_year.year,
                date_debut=admission.doctorate.academic_year.start_date,
                intitule=(
                    admission.doctorate.title_english
                    if get_language() == settings.LANGUAGE_CODE_EN
                    else admission.doctorate.title
                ),
                intitule_fr=admission.doctorate.title,
                intitule_en=admission.doctorate.title_english,
                sigle_entite_gestion=admission.sigle_entite_gestion,  # from PropositionManager annotation
                campus=CampusDTO.from_json_annotation(admission.teaching_campus_info),  # from annotation
                type=admission.doctorate.education_group_type.name,
                campus_inscription=CampusDTO.from_model_object(admission.training.enrollment_campus),
                credits=admission.training.credits,
            ),
            annee_calculee=admission.determined_academic_year and admission.determined_academic_year.year,
            type_demande=admission.type_demande,
            pot_calcule=admission.determined_pool or '',
            date_fin_pot=admission.pool_end_date,  # from annotation
            matricule_candidat=admission.candidate.global_id,
            prenom_candidat=admission.candidate.first_name,
            nom_candidat=admission.candidate.last_name,
            langue_contact_candidat=admission.candidate.language,
            code_secteur_formation=admission.code_secteur_formation,  # from PropositionManager annotation
            intitule_secteur_formation=admission.intitule_secteur_formation,  # from PropositionManager annotation
            commission_proximite=admission.proximity_commission,
            creee_le=admission.created_at,
            statut=admission.status,
            justification=admission.comment,
            type_financement=admission.financing_type,
            type_contrat_travail=admission.financing_work_contract,
            eft=admission.financing_eft,
            bourse_recherche=BourseTranslator.build_dto(admission.international_scholarship)
            if admission.international_scholarship
            else None,
            autre_bourse_recherche=admission.other_international_scholarship,
            bourse_date_debut=admission.scholarship_start_date,
            bourse_date_fin=admission.scholarship_end_date,
            bourse_preuve=admission.scholarship_proof,
            duree_prevue=admission.planned_duration,
            temps_consacre=admission.dedicated_time,
            est_lie_fnrs_fria_fresh_csc=admission.is_fnrs_fria_fresh_csc_linked,
            commentaire_financement=admission.financing_comment,
            titre_projet=admission.project_title,
            resume_projet=admission.project_abstract,
            documents_projet=admission.project_document,
            graphe_gantt=admission.gantt_graph,
            proposition_programme_doctoral=admission.program_proposition,
            projet_formation_complementaire=admission.additional_training_project,
            lettres_recommandation=admission.recommendation_letters,
            langue_redaction_these=admission.thesis_language.code if admission.thesis_language else '',
            institut_these=admission.thesis_institute and admission.thesis_institute.uuid,
            nom_institut_these=admission.thesis_institute and admission.thesis_institute.title or '',
            sigle_institut_these=admission.thesis_institute and admission.thesis_institute.acronym or '',
            lieu_these=admission.thesis_location,
            projet_doctoral_deja_commence=admission.phd_alread_started,
            projet_doctoral_institution=admission.phd_alread_started_institute,
            projet_doctoral_date_debut=admission.work_start_date,
            doctorat_deja_realise=admission.phd_already_done,
            institution=admission.phd_already_done_institution,
            domaine_these=admission.phd_already_done_thesis_domain,
            date_soutenance=admission.phd_already_done_defense_date,
            raison_non_soutenue=admission.phd_already_done_no_defense_reason,
            nationalite_candidat=admission.candidate.country_of_citizenship
            and getattr(
                admission.candidate.country_of_citizenship,
                'name' if get_language() == settings.LANGUAGE_CODE_FR else 'name_en',
            ),
            modifiee_le=admission.modified_at,
            fiche_archive_signatures_envoyees=admission.archived_record_signatures_sent,
            erreurs=admission.detailed_status or [],
            reponses_questions_specifiques=admission.specific_question_answers,
            curriculum=admission.curriculum,
            elements_confirmation=admission.confirmation_elements,
            soumise_le=admission.submitted_at,
            pdf_recapitulatif=admission.pdf_recap,
            documents_demandes=admission.requested_documents,
            documents_libres_fac_uclouvain=admission.uclouvain_fac_documents,
            documents_libres_sic_uclouvain=admission.uclouvain_sic_documents,
            financabilite_regle_calcule=admission.financability_computed_rule,
            financabilite_regle_calcule_situation=admission.financability_computed_rule_situation,
            financabilite_regle_calcule_le=admission.financability_computed_rule_on,
            financabilite_regle=admission.financability_rule,
            financabilite_regle_etabli_par=admission.financability_rule_established_by.uuid
            if admission.financability_rule_established_by
            else '',
            financabilite_regle_etabli_le=admission.financability_rule_established_on,
            financabilite_derogation_statut=admission.financability_dispensation_status,
            financabilite_derogation_premiere_notification_le=(
                admission.financability_dispensation_first_notification_on
            ),
            financabilite_derogation_premiere_notification_par=(
                admission.financability_dispensation_first_notification_by.global_id
                if admission.financability_dispensation_first_notification_by
                else ''
            ),
            financabilite_derogation_derniere_notification_le=(
                admission.financability_dispensation_last_notification_on
            ),
            financabilite_derogation_derniere_notification_par=(
                admission.financability_dispensation_last_notification_by.global_id
                if admission.financability_dispensation_last_notification_by
                else ''
            ),
            certificat_approbation_fac=admission.fac_approval_certificate,
            certificat_approbation_sic=admission.sic_approval_certificate,
            certificat_approbation_sic_annexe=admission.sic_annexe_approval_certificate,
            doit_fournir_visa_etudes=admission.must_provide_student_visa_d,
            visa_etudes_d=admission.student_visa_d,
            certificat_autorisation_signe=admission.signed_enrollment_authorization,
        )

    @classmethod
    def _load_dto_for_gestionnaire(
        cls,
        admission: PropositionProxy,
        prerequisite_courses: List[Union['PartimSearchDTO', 'LearningUnitSearchDTO']],
    ) -> 'PropositionGestionnaireDTO':
        proposition = cls._load_dto(admission)

        country_of_citizenship_info = (
            dict(
                nationalite_candidat_fr=admission.candidate.country_of_citizenship.name,
                nationalite_candidat_en=admission.candidate.country_of_citizenship.name_en,
                nationalite_ue_candidat=admission.candidate.country_of_citizenship.european_union,
                nationalite_candidat_code_iso=admission.candidate.country_of_citizenship.iso_code,
            )
            if admission.candidate.country_of_citizenship
            else dict(
                nationalite_candidat_fr='',
                nationalite_candidat_en='',
                nationalite_ue_candidat=None,
                nationalite_candidat_code_iso='',
            )
        )

        return PropositionGestionnaireDTO(
            **dto_to_dict(proposition),
            **country_of_citizenship_info,
            date_changement_statut=admission.status_updated_at,  # from annotation
            candidat_a_plusieurs_demandes=admission.has_several_admissions_in_progress,
            genre_candidat=admission.candidate.gender,
            noma_candidat=admission.student_registration_id or '',  # from annotation
            photo_identite_candidat=admission.candidate.id_photo,
            adresse_email_candidat=admission.candidate.private_email,
            cotutelle=CotutelleDTO(
                cotutelle=admission.cotutelle,
                motivation=admission.cotutelle_motivation,
                institution_fwb=admission.cotutelle_institution_fwb,
                institution=admission.cotutelle_institution,
                demande_ouverture=admission.cotutelle_opening_request,
                convention=admission.cotutelle_convention,
                autres_documents=admission.cotutelle_other_documents,
                autre_institution=bool(
                    admission.cotutelle_other_institution_name or admission.cotutelle_other_institution_address
                ),
                autre_institution_nom=admission.cotutelle_other_institution_name,
                autre_institution_adresse=admission.cotutelle_other_institution_address,
            )
            if admission.cotutelle
            else None,
            profil_soumis_candidat=ProfilCandidatDTO.from_dict(
                dict_profile=admission.submitted_profile,
                nom_pays_nationalite=admission.submitted_profile_country_of_citizenship_name or '',  # from annotation
                nom_pays_adresse=admission.submitted_profile_country_name or '',  # from annotation
            )
            if admission.submitted_profile
            else None,
            motifs_refus=[
                MotifRefusDTO(motif=mark_safe(reason.name), categorie=reason.category.name)
                for reason in admission.refusal_reasons.all()
            ]
            + [
                MotifRefusDTO(motif=reason, categorie=pgettext('admission', 'Other reasons'))
                for reason in admission.other_refusal_reasons
            ],
            avec_complements_formation=admission.with_prerequisite_courses,
            complements_formation=prerequisite_courses,
            commentaire_complements_formation=admission.prerequisite_courses_fac_comment,
            nombre_annees_prevoir_programme=admission.program_planned_years_number,
            nom_personne_contact_programme_annuel_annuel=admission.annual_program_contact_person_name,
            email_personne_contact_programme_annuel_annuel=admission.annual_program_contact_person_email,
            commentaire_programme_conjoint=admission.join_program_fac_comment,
            condition_acces=admission.admission_requirement,
            millesime_condition_acces=admission.admission_requirement_year.year
            if admission.admission_requirement_year
            else None,
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
            admission = PropositionProxy.objects.for_manager_dto().get(uuid=entity_id.uuid)
        except PropositionProxy.DoesNotExist:
            raise PropositionNonTrouveeException

        prerequisite_courses = unites_enseignement_translator.search(
            code_annee_valeurs=admission.prerequisite_courses.all().values_list('acronym', 'academic_year__year'),
        )

        return cls._load_dto_for_gestionnaire(admission, prerequisite_courses)
