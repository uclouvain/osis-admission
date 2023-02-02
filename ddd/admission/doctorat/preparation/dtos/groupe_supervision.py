# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from typing import List, Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PromoteurDTO(interface.DTO):
    uuid: str
    matricule: Optional[str]
    nom: str
    prenom: str
    email: str
    est_docteur: bool = False
    institution: str = ""
    ville: str = ""
    pays: str = ""
    est_externe: bool = False


@attr.dataclass(frozen=True, slots=True)
class MembreCADTO(interface.DTO):
    uuid: str
    matricule: Optional[str]
    nom: str
    prenom: str
    email: str
    est_docteur: bool = False
    institution: str = ""
    ville: str = ""
    pays: str = ""
    est_externe: bool = False


@attr.dataclass(frozen=True, slots=True)
class DetailSignaturePromoteurDTO(interface.DTO):
    promoteur: PromoteurDTO
    statut: str
    date: Optional[datetime.datetime] = None
    commentaire_externe: Optional[str] = ''
    commentaire_interne: Optional[str] = ''
    motif_refus: Optional[str] = ''
    pdf: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class DetailSignatureMembreCADTO(interface.DTO):
    membre_CA: MembreCADTO
    statut: str
    date: Optional[datetime.datetime] = None
    commentaire_externe: Optional[str] = ''
    commentaire_interne: Optional[str] = ''
    motif_refus: Optional[str] = ''
    pdf: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class AvisDTO(interface.DTO):
    etat: str
    commentaire_externe: Optional[str] = ''
    commentaire_interne: Optional[str] = ''
    motif_refus: Optional[str] = ''
    pdf: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class CotutelleDTO(interface.DTO):
    cotutelle: Optional[bool]
    motivation: Optional[str]
    institution_fwb: Optional[bool]
    institution: Optional[str]
    demande_ouverture: List[str]
    convention: List[str]
    autres_documents: List[str]


@attr.dataclass(frozen=True, slots=True)
class GroupeDeSupervisionDTO(interface.DTO):
    signatures_promoteurs: List[DetailSignaturePromoteurDTO] = attr.Factory(list)
    signatures_membres_CA: List[DetailSignatureMembreCADTO] = attr.Factory(list)
    promoteur_reference: Optional[str] = None
    cotutelle: Optional[CotutelleDTO] = None
