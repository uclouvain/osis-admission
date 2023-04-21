##############################################################################
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
##############################################################################
import datetime
from typing import Optional, List

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class AuteurDTO(interface.DTO):
    matricule: str
    nom: str
    prenom: str
    est_candidat: bool


@attr.dataclass(frozen=True, slots=True)
class EmplacementDocumentDTO(interface.Entity):
    identifiant: str
    libelle: str
    uuids: List[str]
    auteur: str
    type: str
    statut: str
    justification_gestionnaire: str
    soumis_le: Optional[datetime.datetime]
    reclame_le: Optional[datetime.datetime]
    derniere_action_le: Optional[datetime.datetime]
    a_echeance_le: Optional[datetime.datetime]
    onglet: str
    nom_onglet: str
    uuid_demande: str
