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
from dataclasses import dataclass
from typing import List, Optional

from admission.ddd.projet_doctoral.preparation.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.projet_doctoral.preparation.dtos import PropositionDTO
from admission.ddd.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.projet_doctoral.preparation.test.factory.proposition import (
    PropositionAdmissionECGE3DPMinimaleFactory,
    PropositionAdmissionESP3DPMinimaleFactory,
    PropositionAdmissionSC3DPAvecMembresEtCotutelleFactory,
    PropositionAdmissionSC3DPAvecMembresFactory,
    PropositionAdmissionSC3DPAvecMembresInvitesFactory,
    PropositionAdmissionSC3DPAvecPromoteurDejaApprouveFactory,
    PropositionAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory,
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    PropositionAdmissionSC3DPMinimaleCotutelleAvecPromoteurExterneFactory,
    PropositionAdmissionSC3DPMinimaleCotutelleSansPromoteurExterneFactory,
    PropositionAdmissionSC3DPMinimaleFactory,
    PropositionAdmissionSC3DPMinimaleSansCotutelleFactory,
    PropositionAdmissionSC3DPMinimaleSansDetailProjetFactory,
    PropositionAdmissionSC3DPMinimaleSansFinancementFactory,
    PropositionAdmissionSC3DPSansMembreCAFactory,
    PropositionAdmissionSC3DPSansPromoteurFactory,
    PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    PropositionPreAdmissionSC3DPMinimaleFactory,
)
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


@dataclass
class _Candidat:
    prenom: str
    nom: str
    nationalite: str


@dataclass
class _Doctorat:
    intitule: str
    code_secteur: str
    intitule_secteur: str


class PropositionInMemoryRepository(InMemoryGenericRepository, IPropositionRepository):
    doctorats = {
        ("SC3DP", 2020): _Doctorat(
            intitule="Doctorat en sciences",
            code_secteur="SST",
            intitule_secteur="Secteur des sciences et technologies",
        ),
        ("ECGE3DP", 2020): _Doctorat(
            intitule="Doctorat en sciences économiques et de gestion",
            code_secteur="SSH",
            intitule_secteur="Secteur des sciences humaines",
        ),
        ("ESP3DP", 2020): _Doctorat(
            intitule="Doctorat en sciences de la santé publique",
            code_secteur="SSS",
            intitule_secteur="Secteur des sciences de la santé",
        ),
    }
    candidats = {
        "0123456789": _Candidat("Jean", "Dupont", "France"),
        "0000000001": _Candidat("Michel", "Durand", "Belgique"),
        "candidat": _Candidat("Pierre", "Dupond", "Belgique"),
    }
    entities: List['Proposition'] = []

    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        proposition = super().get(entity_id)
        if not proposition:
            raise PropositionNonTrouveeException
        return proposition

    @classmethod
    def reset(cls):
        cls.entities = [
            PropositionAdmissionSC3DPMinimaleFactory(),
            PropositionAdmissionSC3DPAvecMembresFactory(),
            PropositionAdmissionSC3DPAvecMembresEtCotutelleFactory(),
            PropositionAdmissionSC3DPAvecMembresInvitesFactory(),
            PropositionAdmissionECGE3DPMinimaleFactory(),
            PropositionPreAdmissionSC3DPMinimaleFactory(),
            PropositionAdmissionSC3DPMinimaleSansDetailProjetFactory(),
            PropositionAdmissionSC3DPMinimaleSansFinancementFactory(),
            PropositionAdmissionSC3DPMinimaleSansCotutelleFactory(),
            PropositionAdmissionSC3DPMinimaleCotutelleSansPromoteurExterneFactory(),
            PropositionAdmissionSC3DPMinimaleCotutelleAvecPromoteurExterneFactory(),
            PropositionAdmissionSC3DPSansPromoteurFactory(),
            PropositionAdmissionSC3DPSansMembreCAFactory(),
            PropositionAdmissionESP3DPMinimaleFactory(),
            PropositionAdmissionSC3DPAvecPromoteurDejaApprouveFactory(),
            PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
            PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
            PropositionAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory(),
        ]

    @classmethod
    def save(cls, entity: 'Proposition') -> None:
        try:
            super().save(entity)
        except PropositionNonTrouveeException:
            cls.entities.append(entity)

    @classmethod
    def search(
        cls,
        entity_ids: Optional[List['PropositionIdentity']] = None,
        matricule_candidat: str = None,
        **kwargs,
    ) -> List['Proposition']:
        returned = cls.entities
        if matricule_candidat:
            returned = filter(lambda p: p.matricule_candidat == matricule_candidat, returned)
        if entity_ids:  # pragma: no cover
            returned = filter(lambda p: p.entity_id in entity_ids, returned)
        return list(returned)

    @classmethod
    def get_next_reference(cls):
        return len(cls.entities) + 1

    @classmethod
    def search_dto(
        cls,
        numero: Optional[str] = '',
        matricule_candidat: Optional[str] = '',
        etat: Optional[str] = '',
        nationalite: Optional[str] = '',
        type: Optional[str] = '',
        cdds: Optional[List[str]] = None,
        commission_proximite: Optional[str] = '',
        annee_academique: Optional[int] = None,
        sigles_formations: Optional[List[str]] = None,
        financement: Optional[str] = '',
        type_contrat_travail: Optional[str] = '',
        bourse_recherche: Optional[str] = '',
        matricule_promoteur: Optional[str] = '',
        cotutelle: Optional[bool] = None,
        entity_ids: Optional[List['PropositionIdentity']] = None,
    ) -> List['PropositionDTO']:
        returned = cls.entities
        if matricule_candidat:
            returned = filter(lambda p: p.matricule_candidat == matricule_candidat, returned)
        if numero:
            returned = filter(lambda p: p.reference == numero, returned)
        if type:
            returned = filter(lambda p: p.type_admission.name == type, returned)
        if entity_ids is not None:
            returned = filter(lambda p: p.entity_id in entity_ids, returned)
        return list(cls._load_dto(proposition) for proposition in returned)

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(cls.get(entity_id))

    @classmethod
    def _load_dto(cls, proposition):
        candidat = cls.candidats[proposition.matricule_candidat]
        doctorat = cls.doctorats[(proposition.doctorat_id.sigle, proposition.doctorat_id.annee)]
        return PropositionDTO(
            uuid=proposition.entity_id.uuid,
            type_admission=proposition.type_admission.name,
            reference=proposition.reference,
            sigle_doctorat=proposition.doctorat_id.sigle,
            annee_doctorat=proposition.doctorat_id.annee,
            intitule_doctorat=doctorat.intitule,
            matricule_candidat=proposition.matricule_candidat,
            justification=proposition.justification,
            code_secteur_formation=doctorat.code_secteur,
            commission_proximite=proposition.commission_proximite and proposition.commission_proximite.name or '',
            type_financement=proposition.financement.type and proposition.financement.type.name or '',
            type_contrat_travail=proposition.financement.type_contrat_travail,
            eft=proposition.financement.eft,
            bourse_recherche=proposition.financement.bourse_recherche,
            duree_prevue=proposition.financement.duree_prevue,
            temps_consacre=proposition.financement.temps_consacre,
            titre_projet=proposition.projet.titre,
            resume_projet=proposition.projet.resume,
            documents_projet=proposition.projet.documents,
            graphe_gantt=proposition.projet.graphe_gantt,
            proposition_programme_doctoral=proposition.projet.proposition_programme_doctoral,
            projet_formation_complementaire=proposition.projet.projet_formation_complementaire,
            lettres_recommandation=proposition.projet.lettres_recommandation,
            langue_redaction_these=proposition.projet.langue_redaction_these.name,
            institut_these=proposition.projet.institut_these.uuid if proposition.projet.institut_these else None,
            lieu_these=proposition.projet.lieu_these,
            doctorat_deja_realise=proposition.experience_precedente_recherche.doctorat_deja_realise.name,
            institution=proposition.experience_precedente_recherche.institution,
            date_soutenance=proposition.experience_precedente_recherche.date_soutenance,
            raison_non_soutenue=proposition.experience_precedente_recherche.raison_non_soutenue,
            statut=proposition.statut.name,
            creee_le=proposition.creee_le,
            intitule_secteur_formation=doctorat.intitule_secteur,
            nom_candidat=candidat.nom,
            prenom_candidat=candidat.prenom,
            nationalite_candidat=candidat.nationalite,
            modifiee_le=proposition.modifiee_le,
            erreurs=[],
        )
