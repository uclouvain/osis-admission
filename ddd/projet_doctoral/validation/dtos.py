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

import attr

from osis_common.ddd import interface


@attr.s(frozen=True, slots=True, auto_attribs=True)
class DemandeRechercheDTO(interface.DTO):
    uuid: str
    numero_demande: str
    statut_cdd: str
    statut_sic: str
    statut_demande: str
    nom_candidat: str
    sigle_formation: str
    intitule_formation: str
    nationalite: str
    derniere_modification: datetime.datetime
    date_confirmation: datetime.datetime
    code_bourse: str


@attr.s(frozen=True, slots=True, auto_attribs=True)
class DemandeDTO(interface.DTO):
    uuid: str
    statut_cdd: str
    statut_sic: str
    derniere_modification: datetime.datetime
    # TODO only include info about demande


@attr.s(frozen=True, slots=True, auto_attribs=True)
class RecupererDemandeDTO(interface.DTO):
    uuid: str
    statut_cdd: str
    statut_sic: str
    derniere_modification: datetime.datetime
    # TODO include all info about demande (doctorate and persons too)
