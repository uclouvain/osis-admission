#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from typing import Optional

import attr

from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from osis_common.ddd.interface import Event


@attr.dataclass(frozen=True, slots=True, kw_only=True)
class PropositionDoctoraleSoumiseEvent(Event):
    entity_id: PropositionIdentity
    matricule: str
    nom: str
    prenom: str
    autres_prenoms: Optional[str]
    date_naissance: str
    genre: str
    niss: Optional[str]
    annee: int


@attr.dataclass(frozen=True, slots=True, kw_only=True)
class InscriptionDoctoraleApprouveeParSicEvent(Event):
    entity_id: PropositionIdentity
    type_admission: str
    matricule: str
    objet_message: str
    corps_message: str
    auteur: str


@attr.dataclass(frozen=True, slots=True, kw_only=True)
class AdmissionDoctoraleApprouveeParSicEvent(Event):
    entity_id: PropositionIdentity
    type_admission: str
    matricule: str
    nom: str
    prenom: str
    autres_prenoms: Optional[str]
    date_naissance: str
    genre: str
    niss: Optional[str]
    annee: int


@attr.dataclass(frozen=True, slots=True, kw_only=True)
class FormationDuDossierAdmissionDoctoraleModifieeEvent(Event):
    entity_id: PropositionIdentity
    matricule: str
