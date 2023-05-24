# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class RecupererJuryQuery(interface.QueryRequest):
    uuid_jury: str


@attr.dataclass(frozen=True, slots=True)
class RecupererJuryMembreQuery(interface.QueryRequest):
    uuid_jury: str
    uuid_membre: str


@attr.dataclass(frozen=True, slots=True)
class ModifierJuryCommand(interface.CommandRequest):
    uuid_doctorat: str
    titre_propose: str
    formule_defense: str
    date_indicative: datetime.date
    langue_redaction: str
    langue_soutenance: str
    commentaire: str


@attr.dataclass(frozen=True, slots=True)
class AjouterMembreCommand(interface.CommandRequest):
    uuid_jury: str
    matricule: Optional[str]
    institution: Optional[str]
    autre_institution: Optional[str]
    pays: Optional[str]
    nom: Optional[str]
    prenom: Optional[str]
    titre: Optional[str]
    justification_non_docteur: Optional[str]
    genre: Optional[str]
    email: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class ModifierMembreCommand(interface.CommandRequest):
    uuid_jury: str
    uuid_membre: str
    matricule: Optional[str]
    institution: Optional[str]
    autre_institution: Optional[str]
    pays: Optional[str]
    nom: Optional[str]
    prenom: Optional[str]
    titre: Optional[str]
    justification_non_docteur: Optional[str]
    genre: Optional[str]
    email: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class RetirerMembreCommand(interface.CommandRequest):
    uuid_jury: str
    uuid_membre: str


@attr.dataclass(frozen=True, slots=True)
class ModifierRoleMembreCommand(interface.CommandRequest):
    uuid_jury: str
    uuid_membre: str
    role: str
