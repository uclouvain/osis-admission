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

from datetime import date
from typing import List, Optional

import attr

from admission.ddd.parcours_doctoral.formation.domain.model.enums import ChoixStatutPublication
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class ConferenceDTO(interface.DTO):
    type: str = ""
    nom_manifestation: str = ""
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    nombre_jours: float = 0
    en_ligne: bool = False
    pays: str = ""
    ville: str = ""
    institution_organisatrice: str = ""
    commentaire: str = ""
    site_web: str = ""
    certificat_participation: List[str] = attr.Factory(list)


@attr.dataclass(slots=True, frozen=True)
class ConferenceCommunicationDTO(interface.DTO):
    type: str = ""
    titre: str = ""
    comite_selection: str = ""
    reference_dial: str = ""
    preuve_acceptation: List[str] = attr.Factory(list)
    resume: List[str] = attr.Factory(list)
    attestation_communication: List[str] = attr.Factory(list)
    commentaire: str = ""


@attr.dataclass(slots=True, frozen=True)
class ConferencePublicationDTO(interface.DTO):
    type: str = ""
    intitule: str = ""
    date: Optional[date] = None
    auteurs: str = ""
    role: str = ""
    nom_revue_maison_edition: str = ""
    statut_publication: Optional[ChoixStatutPublication] = None
    preuve_acceptation: List[str] = attr.Factory(list)
    comite_selection: str = ""
    mots_cles: str = ""
    resume: str = ""
    reference_dial: str = ""
    commentaire: str = ""
