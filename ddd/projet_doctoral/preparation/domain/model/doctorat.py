# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import attr

# FIXME should be imported from shared kernel when available
from base.ddd.utils.converters import to_upper_case_converter
from ddd.logic.learning_unit.domain.model.responsible_entity import UCLEntityIdentity
from osis_common.ddd import interface

ENTITY_CDE = 'CDE'
ENTITY_CDSS = 'CDSS'
ENTITY_CLSM = 'CLSM'
SIGLE_SCIENCES = 'SC3DP'


@attr.dataclass(frozen=True, slots=True)
class DoctoratIdentity(interface.EntityIdentity):
    sigle: str = attr.ib(converter=to_upper_case_converter)
    annee: int


@attr.dataclass(slots=True)
class Doctorat(interface.Entity):
    entity_id: 'DoctoratIdentity'
    entite_ucl_id: 'UCLEntityIdentity'

    def est_entite_CDE(self):
        return self.entite_ucl_id.code == ENTITY_CDE

    def est_entite_CDSS(self):
        return self.entite_ucl_id.code == ENTITY_CDSS

    def est_entite_CLSM(self):
        return self.entite_ucl_id.code == ENTITY_CLSM

    def est_domaine_des_sciences(self):
        return self.entity_id.sigle == SIGLE_SCIENCES
