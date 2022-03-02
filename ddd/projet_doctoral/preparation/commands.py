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
import datetime
from typing import List, Optional

import attr

from admission.ddd.projet_doctoral.preparation.domain.model._detail_projet import ChoixLangueRedactionThese
from admission.ddd.projet_doctoral.preparation.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
)
from osis_common.ddd import interface

UUID = str


@attr.dataclass(frozen=True, slots=True)
class InitierPropositionCommand(interface.CommandRequest):
    type_admission: str
    sigle_formation: str
    annee_formation: int
    matricule_candidat: str
    justification: Optional[str] = ''
    commission_proximite: Optional[str] = ''
    type_financement: Optional[str] = ''
    type_contrat_travail: Optional[str] = ''
    eft: Optional[int] = None
    bourse_recherche: Optional[str] = ''
    duree_prevue: Optional[int] = None
    temps_consacre: Optional[int] = None
    titre_projet: Optional[str] = ''
    resume_projet: Optional[str] = ''
    institut_these: Optional[str] = ''
    lieu_these: Optional[str] = ''
    documents_projet: List[str] = attr.Factory(list)
    graphe_gantt: List[str] = attr.Factory(list)
    proposition_programme_doctoral: List[str] = attr.Factory(list)
    projet_formation_complementaire: List[str] = attr.Factory(list)
    lettres_recommandation: List[str] = attr.Factory(list)
    langue_redaction_these: str = ChoixLangueRedactionThese.UNDECIDED.name
    doctorat_deja_realise: str = ChoixDoctoratDejaRealise.NO.name
    institution: Optional[str] = ''
    date_soutenance: Optional[datetime.date] = None
    raison_non_soutenue: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class CompleterPropositionCommand(interface.CommandRequest):
    uuid: str
    type_admission: str
    justification: Optional[str] = ''
    commission_proximite: Optional[str] = ''
    type_financement: Optional[str] = ''
    type_contrat_travail: Optional[str] = ''
    eft: Optional[int] = None
    bourse_recherche: Optional[str] = ''
    duree_prevue: Optional[int] = None
    temps_consacre: Optional[int] = None
    titre_projet: Optional[str] = ''
    resume_projet: Optional[str] = ''
    documents_projet: List[str] = attr.Factory(list)
    graphe_gantt: List[str] = attr.Factory(list)
    proposition_programme_doctoral: List[str] = attr.Factory(list)
    projet_formation_complementaire: List[str] = attr.Factory(list)
    lettres_recommandation: List[str] = attr.Factory(list)
    langue_redaction_these: str = ChoixLangueRedactionThese.UNDECIDED.name
    institut_these: Optional[str] = ''
    lieu_these: Optional[str] = ''
    doctorat_deja_realise: str = ChoixDoctoratDejaRealise.NO.name
    institution: Optional[str] = ''
    date_soutenance: Optional[datetime.date] = None
    raison_non_soutenue: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class SearchDoctoratCommand(interface.QueryRequest):
    sigle_secteur_entite_gestion: str


@attr.dataclass(frozen=True, slots=True)
class IdentifierPromoteurCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str


@attr.dataclass(frozen=True, slots=True)
class IdentifierMembreCACommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str


@attr.dataclass(frozen=True, slots=True)
class DemanderSignaturesCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class VerifierPropositionCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class VerifierProjetCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerPromoteurCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerMembreCACommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str


@attr.dataclass(frozen=True, slots=True)
class ApprouverPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str
    institut_these: Optional[str] = ''
    commentaire_interne: Optional[str] = ''
    commentaire_externe: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class RefuserPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str
    motif_refus: str
    commentaire_interne: Optional[str] = ''
    commentaire_externe: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class SoumettrePropositionCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class DefinirCotutelleCommand(interface.CommandRequest):
    uuid_proposition: str
    motivation: Optional[str] = ''
    institution: Optional[str] = ''
    demande_ouverture: List[str] = attr.Factory(list)
    convention: List[str] = attr.Factory(list)
    autres_documents: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class SearchPropositionsCandidatCommand(interface.QueryRequest):
    matricule_candidat: str


@attr.dataclass(frozen=True, slots=True)
class SearchPropositionsSuperviseesCommand(interface.QueryRequest):
    matricule_membre: str


@attr.dataclass(frozen=True, slots=True)
class GetPropositionCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class GetGroupeDeSupervisionCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class GetCotutelleCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerPropositionCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class ApprouverPropositionParPdfCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str
    pdf: List[str] = attr.Factory(list)
