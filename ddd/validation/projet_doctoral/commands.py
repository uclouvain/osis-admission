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
from datetime import datetime
from typing import Optional

import attr

from osis_common.ddd import interface


@attr.s(frozen=True, slots=True, auto_attribs=True)
class FiltrerDemandesQuery(interface.CommandRequest):
    numero: Optional[str] = ''
    etat_cdd: Optional[str] = ''
    etat_sic: Optional[str] = ''
    nom_prenom_email: Optional[str] = ''
    nationalite: Optional[str] = ''
    type: Optional[str] = ''
    commission_proximite: Optional[str] = ''
    annee_academique: Optional[int] = None
    sigle_formation: Optional[str] = ''
    financement: Optional[str] = ''
    matricule_promoteur: Optional[str] = ''
    cotutelle: Optional[bool] = None
    date_pre_admission_debut: Optional[datetime] = None
    date_pre_admission_fin: Optional[datetime] = None


@attr.s(frozen=True, slots=True, auto_attribs=True)
class RecupererDemandeQuery(interface.CommandRequest):
    numero: Optional[str] = ''


@attr.s(frozen=True, slots=True, auto_attribs=True)
class RefuserDemandeCddCommand(interface.CommandRequest):
    numero: Optional[str] = ''
