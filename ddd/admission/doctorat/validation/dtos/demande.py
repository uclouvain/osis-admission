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
from typing import Optional

import attr

from osis_common.ddd import interface
from .profil_candidat import ProfilCandidatDTO


@attr.dataclass(frozen=True, slots=True)
class DemandeRechercheDTO(interface.DTO):
    uuid: str
    numero_demande: str
    statut_cdd: Optional[str]
    statut_sic: Optional[str]
    statut_demande: str
    nom_candidat: str
    formation: str
    nationalite: str
    derniere_modification: datetime.datetime
    date_confirmation: Optional[datetime.datetime]
    code_bourse: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class DemandeDTO(interface.DTO):
    uuid: str
    statut_cdd: str
    statut_sic: str
    pre_admission_acceptee_le: Optional[datetime.datetime]
    admission_acceptee_le: Optional[datetime.datetime]
    derniere_modification: datetime.datetime
    pre_admission_confirmee_le: Optional[datetime.datetime]
    admission_confirmee_le: Optional[datetime.datetime]
    profil_candidat: ProfilCandidatDTO
    # TODO only include info about demande


@attr.dataclass(frozen=True, slots=True)
class RecupererDemandeDTO(interface.DTO):
    uuid: str
    statut_cdd: str
    statut_sic: str
    derniere_modification: datetime.datetime
    pre_admission_acceptee_le: Optional[datetime.datetime]
    admission_acceptee_le: Optional[datetime.datetime]
    pre_admission_confirmee_le: Optional[datetime.datetime]
    admission_confirmee_le: Optional[datetime.datetime]
    # TODO include all info about demande (doctorate and persons too)
