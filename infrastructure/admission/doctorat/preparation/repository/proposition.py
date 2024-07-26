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
from typing import List, Optional

from django.conf import settings
from django.db.models import OuterRef, Subquery
from django.utils.translation import get_language

from admission.auth.roles.candidate import Candidate
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
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
    PropositionIdentity,
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
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.model.bourse import BourseIdentity
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.infrastructure.admission.doctorat.preparation.repository._comptabilite import (
    get_accounting_from_admission,
)
from admission.infrastructure.admission.domain.service.bourse import BourseTranslator
from admission.infrastructure.admission.repository.proposition import GlobalPropositionRepository
from admission.infrastructure.utils import dto_to_dict
from admission.models import Accounting, DoctorateAdmission
from admission.models.doctorate import PropositionProxy
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.person import Person
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
    )


def load_admissions(matricule: Optional[str] = None, ids: Optional[List[str]] = None) -> List['Proposition']:
    qs = []
    if matricule is not None:
        qs = PropositionProxy.objects.filter(candidate__global_id=matricule)
    elif ids is not None:  # pragma: no branch
        qs = PropositionProxy.objects.filter(uuid__in=ids)

    return [_instantiate_admission(a) for a in qs]


class PropositionRepository(GlobalPropositionRepository, IPropositionRepository):
    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        try:
            return _instantiate_admission(PropositionProxy.objects.get(uuid=entity_id.uuid))
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
                    ]
                    if matricule
                ]
            )
        }

        candidate = persons[entity.matricule_candidat]

        last_update_author = (
            persons[entity.auteur_derniere_modification] if entity.auteur_derniere_modification in persons else None
        )

        admission, _ = DoctorateAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'reference': entity.reference,
                'type': entity.type_admission.name,
                'status': entity.statut.name,
                'comment': entity.justification,
                'candidate': candidate,
                'proximity_commission': entity.commission_proximite and entity.commission_proximite.name or '',
                'doctorate': doctorate,
                'determined_academic_year': (
                    entity.annee_calculee and AcademicYear.objects.get(year=entity.annee_calculee)
                ),
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
            },
        )
        Candidate.objects.get_or_create(person=candidate)

        cls._sauvegarder_comptabilite(admission, entity)

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
        qs = PropositionProxy.objects.all()
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
        return cls._load_dto(PropositionProxy.objects.get(uuid=entity_id.uuid))

    @classmethod
    def _load_dto(cls, admission: DoctorateAdmission) -> 'PropositionDTO':
        return PropositionDTO(
            uuid=admission.uuid,
            reference=admission.formatted_reference,
            type_admission=admission.type,
            doctorat=DoctoratDTO(
                sigle=admission.doctorate.acronym,
                code=admission.doctorate.partial_acronym,
                annee=admission.doctorate.academic_year.year,
                intitule=(
                    admission.doctorate.title_english
                    if get_language() == settings.LANGUAGE_CODE_EN
                    else admission.doctorate.title
                ),
                sigle_entite_gestion=admission.sigle_entite_gestion,  # from PropositionManager annotation
                campus=admission.teaching_campus or '',  # from PropositionManager annotation
                type=admission.doctorate.education_group_type.name,
                campus_inscription=admission.doctorate.enrollment_campus.name,
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
            soumise_le=admission.submitted_at or admission.pre_admission_submission_date,
            pdf_recapitulatif=admission.pdf_recap,
            documents_demandes=admission.requested_documents,
            documents_libres_fac_uclouvain=admission.uclouvain_fac_documents,
            documents_libres_sic_uclouvain=admission.uclouvain_sic_documents,
        )

    @classmethod
    def _load_dto_for_gestionnaire(
        cls,
        admission: PropositionProxy,
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
                autre_institution_adresse=admission.cotutelle_other_institution_address
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
        )

    @classmethod
    def get_dto_for_gestionnaire(
        cls,
        entity_id: 'PropositionIdentity',
    ) -> 'PropositionGestionnaireDTO':
        try:
            admission = (
                PropositionProxy.objects.annotate_with_student_registration_id()
                .annotate_several_admissions_in_progress()
                .annotate_submitted_profile_countries_names()
                .annotate_last_status_update()
                .get(uuid=entity_id.uuid)
            )
        except PropositionProxy.DoesNotExist:
            raise PropositionNonTrouveeException

        return cls._load_dto_for_gestionnaire(admission)
