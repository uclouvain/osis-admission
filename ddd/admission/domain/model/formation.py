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
import attr

from admission.ddd import PREFIXES_DOMAINES_FORMATIONS_DENT_MED
from admission.ddd.admission.domain.enums import TypeFormation
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.ddd.utils.converters import to_upper_case_converter
from base.models.enums.education_group_types import TrainingType
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class FormationIdentity(interface.EntityIdentity):
    sigle: str = attr.ib(converter=to_upper_case_converter)
    annee: int


def est_formation_medecine_ou_dentisterie(code_domaine: str) -> bool:
    return code_domaine[:2] in PREFIXES_DOMAINES_FORMATIONS_DENT_MED


@attr.dataclass(frozen=True, slots=True)
class Formation(interface.Entity):
    entity_id: FormationIdentity
    type: TrainingType
    code_domaine: str
    campus: str

    @property
    def type_formation(self) -> TypeFormation:
        return TypeFormation[AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE[self.type.name]]

    @property
    def est_formation_medecine_ou_dentisterie(self) -> bool:
        return est_formation_medecine_ou_dentisterie(self.code_domaine)
