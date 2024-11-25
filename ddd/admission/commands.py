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
from typing import Optional, List, Dict

import attr

from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.ddd.interface import SortedQueryRequest
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class ListerToutesDemandesQuery(SortedQueryRequest):
    annee_academique: Optional[int] = None
    numero: Optional[int] = None
    noma: Optional[str] = ''
    matricule_candidat: Optional[str] = ''
    etats: Optional[List[str]] = None
    type: Optional[str] = ''
    site_inscription: Optional[str] = ''
    entites: Optional[List[str]] = None
    types_formation: Optional[List[str]] = None
    formation: Optional[str] = ''
    bourse_internationale: Optional[str] = ''
    bourse_erasmus_mundus: Optional[str] = ''
    bourse_double_diplomation: Optional[str] = ''
    quarantaine: Optional[bool] = None
    tardif_modif_reorientation: Optional[str] = ''
    demandeur: Optional[str] = ''
    mode_filtres_etats_checklist: Optional[str] = ''
    filtres_etats_checklist: Optional[Dict[str, List[str]]] = ''


@attr.dataclass(frozen=True, slots=True)
class RecupererQuestionsSpecifiquesQuery(interface.QueryRequest):
    uuid_proposition: str
    type: Optional[str] = None
    requis: Optional[bool] = None
    onglets: List[str] = None


@attr.dataclass(frozen=True, slots=True)
class InitialiserEmplacementDocumentLibreNonReclamableCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_document: str
    type_emplacement: str
    libelle: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class InitialiserEmplacementDocumentLibreAReclamerCommand(interface.CommandRequest):
    uuid_proposition: str
    type_emplacement: str
    libelle_fr: str
    libelle_en: str
    statut_reclamation: str
    raison: str
    auteur: str
    uuid_document: str = ''
    onglet_checklist_associe: str = ''


@attr.dataclass(frozen=True, slots=True)
class InitialiserEmplacementDocumentAReclamerCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiant_emplacement: str
    type_emplacement: str
    raison: str
    auteur: str
    statut_reclamation: str


@attr.dataclass(frozen=True, slots=True)
class ModifierReclamationEmplacementDocumentCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiant_emplacement: str
    raison: str
    auteur: str
    statut_reclamation: str


@attr.dataclass(frozen=True, slots=True)
class AnnulerReclamationEmplacementDocumentCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiant_emplacement: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerEmplacementDocumentCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiant_emplacement: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class RemplacerEmplacementDocumentCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiant_emplacement: str
    uuid_document: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class RemplirEmplacementDocumentParGestionnaireCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiant_emplacement: str
    uuid_document: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class RechercherParcoursAnterieurQuery(interface.QueryRequest):
    global_id: str
    uuid_proposition: str
    experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES


@attr.dataclass(frozen=True, slots=True)
class RecupererExperienceAcademiqueQuery(interface.QueryRequest):
    global_id: str
    uuid_proposition: str
    uuid_experience: str


@attr.dataclass(frozen=True, slots=True)
class RecupererExperienceNonAcademiqueQuery(interface.QueryRequest):
    global_id: str
    uuid_proposition: str
    uuid_experience: str

@attr.dataclass(frozen=True, slots=True)
class RecupererEtudesSecondairesQuery(interface.QueryRequest):
    matricule_candidat: str


@attr.dataclass(frozen=True, slots=True)
class RecupererConnaissancesLanguesQuery(interface.QueryRequest):
    matricule_candidat: str


@attr.dataclass(frozen=True, slots=True)
class RecupererTitresAccesSelectionnablesPropositionQuery(interface.QueryRequest):
    uuid_proposition: str
    seulement_selectionnes: Optional[bool] = None


@attr.dataclass(frozen=True, slots=True)
class SpecifierExperienceEnTantQueTitreAccesCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_experience: str
    type_experience: str
    selectionne: bool
