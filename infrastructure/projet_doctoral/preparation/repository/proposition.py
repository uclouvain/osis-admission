# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db import connection

from admission.auth.roles.candidate import Candidate
from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.doctorate import REFERENCE_SEQ_NAME
from admission.ddd.projet_doctoral.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.projet_doctoral.preparation.domain.model._detail_projet import (
    ChoixLangueRedactionThese,
    DetailProjet,
)
from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutProposition,
    ChoixTypeAdmission,
)
from admission.ddd.projet_doctoral.preparation.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
    ExperiencePrecedenteRecherche,
)
from admission.ddd.projet_doctoral.preparation.domain.model._financement import ChoixTypeFinancement, Financement
from admission.ddd.projet_doctoral.preparation.domain.model._institut import InstitutIdentity
from admission.ddd.projet_doctoral.preparation.domain.model.doctorat import DoctoratIdentity
from admission.ddd.projet_doctoral.preparation.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.projet_doctoral.preparation.dtos import PropositionCandidatDTO, PropositionDTO
from admission.ddd.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.person import Person
from osis_common.ddd.interface import ApplicationService


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
        doctorat_id=DoctoratIdentity(admission.doctorate.acronym, admission.doctorate.academic_year.year),
        matricule_candidat=admission.candidate.global_id,
        reference=admission.reference,
        projet=DetailProjet(
            titre=admission.project_title,
            resume=admission.project_abstract,
            documents=admission.project_document,
            langue_redaction_these=ChoixLangueRedactionThese[admission.thesis_language],
            institut_these=InstitutIdentity(admission.thesis_institute.uuid) if admission.thesis_institute_id else None,
            lieu_these=admission.thesis_location,
            graphe_gantt=admission.gantt_graph,
            proposition_programme_doctoral=admission.program_proposition,
            projet_formation_complementaire=admission.additional_training_project,
            lettres_recommandation=admission.recommendation_letters,
        ),
        justification=admission.comment,
        statut=ChoixStatutProposition[admission.status],
        financement=Financement(
            type=ChoixTypeFinancement[admission.financing_type] if admission.financing_type else None,
            type_contrat_travail=admission.financing_work_contract,
            eft=admission.financing_eft,
            bourse_recherche=admission.scholarship_grant,
            duree_prevue=admission.planned_duration,
            temps_consacre=admission.dedicated_time,
        ),
        experience_precedente_recherche=ExperiencePrecedenteRecherche(
            doctorat_deja_realise=ChoixDoctoratDejaRealise[admission.phd_already_done],
            institution=admission.phd_already_done_institution,
            date_soutenance=admission.phd_already_done_defense_date,
            raison_non_soutenue=admission.phd_already_done_no_defense_reason,
        ),
        creee_le=admission.created,
        date_soumission_admission=admission.admission_submission_date,
        date_soumission_pre_admission=admission.pre_admission_submission_date,
    )


def _get_queryset():
    return DoctorateAdmission.objects.all().select_related(
        'doctorate__academic_year',
        'candidate',
        'thesis_institute',
    )


def load_admissions(matricule: Optional[str] = None, ids: Optional[List[str]] = None) -> List['Proposition']:
    qs = []
    if matricule is not None:
        qs = _get_queryset().filter(candidate__global_id=matricule)
    elif ids is not None:  # pragma: no branch
        qs = _get_queryset().filter(uuid__in=ids)

    return [_instantiate_admission(a) for a in qs]


class PropositionRepository(IPropositionRepository):
    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        try:
            return _instantiate_admission(_get_queryset().get(uuid=entity_id.uuid))
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
    def get_next_reference(cls) -> int:
        cursor = connection.cursor()
        cursor.execute("SELECT NEXTVAL('%(sequence)s')" % {'sequence': REFERENCE_SEQ_NAME})
        return cursor.fetchone()[0]

    @classmethod
    def save(cls, entity: 'Proposition') -> None:
        doctorate = EducationGroupYear.objects.get(
            acronym=entity.sigle_formation,
            academic_year__year=entity.annee,
        )
        candidate = Person.objects.get(global_id=entity.matricule_candidat)
        DoctorateAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'reference': entity.reference,
                'type': entity.type_admission.name,
                'status': entity.statut.name,
                'comment': entity.justification,
                'candidate': candidate,
                'proximity_commission': entity.commission_proximite and entity.commission_proximite.name or '',
                'doctorate': doctorate,
                'financing_type': entity.financement.type and entity.financement.type.name or '',
                'financing_work_contract': entity.financement.type_contrat_travail,
                'financing_eft': entity.financement.eft,
                'scholarship_grant': entity.financement.bourse_recherche,
                'planned_duration': entity.financement.duree_prevue,
                'dedicated_time': entity.financement.temps_consacre,
                'project_title': entity.projet.titre,
                'project_abstract': entity.projet.resume,
                'thesis_language': entity.projet.langue_redaction_these.name,
                'thesis_institute': (
                    EntityVersion.objects.get(uuid=entity.projet.institut_these.uuid)
                    if entity.projet.institut_these
                    else None
                ),
                'thesis_location': entity.projet.lieu_these,
                'project_document': entity.projet.documents,
                'gantt_graph': entity.projet.graphe_gantt,
                'program_proposition': entity.projet.proposition_programme_doctoral,
                'additional_training_project': entity.projet.projet_formation_complementaire,
                'recommendation_letters': entity.projet.lettres_recommandation,
                'phd_already_done': entity.experience_precedente_recherche.doctorat_deja_realise.name,
                'phd_already_done_institution': entity.experience_precedente_recherche.institution,
                'phd_already_done_defense_date': entity.experience_precedente_recherche.date_soutenance,
                'phd_already_done_no_defense_reason': entity.experience_precedente_recherche.raison_non_soutenue,
                'pre_admission_submission_date': entity.date_soumission_pre_admission,
                'admission_submission_date': entity.date_soumission_admission,
            },
        )
        Candidate.objects.get_or_create(person=candidate)

    @classmethod
    def search_dto(
        cls,
        numero: Optional[str] = '',
        matricule_candidat: Optional[str] = '',
        etat: Optional[str] = '',
        nationalite: Optional[str] = '',
        type: Optional[str] = '',
        commission_proximite: Optional[str] = '',
        annee_academique: Optional[str] = '',
        sigle_formation: Optional[str] = '',
        financement: Optional[str] = '',
        matricule_promoteur: Optional[str] = '',
        cotutelle: Optional[bool] = None,
    ) -> List['PropositionCandidatDTO']:
        qs = _get_queryset()
        if numero:
            qs = qs.filter(reference=numero)
        if matricule_candidat is not None:
            qs = qs.filter(candidate__global_id=matricule_candidat)
        if etat:  # code enum
            qs = qs.filter(status=etat)
        # TODO search in profile json field
        # if nationalite:  # code pays
        #     qs = qs.filter(submitted_profile__coordinates__country=nationalite)
        if type:
            qs = qs.filter(type=type)
        if commission_proximite:
            qs = qs.filter(proximity_comission=commission_proximite)
        if annee_academique:
            qs = qs.filter(doctorate__academic_year__year=annee_academique)
        if sigle_formation:
            qs = qs.filter(doctorate__acronym=sigle_formation)
        if financement:
            qs = qs.filter(financing_type=financement)
        if matricule_promoteur:
            qs = qs.filter(supervision_group__actors__person__global_id=matricule_promoteur)
        if cotutelle is not None:
            qs = qs.filter(cotutelle=cotutelle)

        return [
            PropositionCandidatDTO(
                uuid=admission.uuid,
                reference=admission.reference,
                type_admission=admission.type,
                sigle_doctorat=admission.doctorate.acronym,
                intitule_doctorat_fr=admission.doctorate.title,
                intitule_doctorat_en=admission.doctorate.title_english,
                matricule_candidat=admission.candidate.global_id,
                prenom_candidat=admission.candidate.first_name,
                nom_candidat=admission.candidate.last_name,
                code_secteur_formation="TODO",  # TODO
                intitule_secteur_formation="TODO",
                commission_proximite=admission.proximity_commission,
                creee_le=admission.created,
                statut=admission.status,
            )
            for admission in qs
        ]

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        raise NotImplementedError
