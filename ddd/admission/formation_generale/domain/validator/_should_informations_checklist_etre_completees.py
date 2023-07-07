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

from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    MotifRefusFacultaireNonSpecifieException,
    InformationsAcceptationFacultaireNonSpecifieesException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldSpecifierMotifRefusFacultaire(BusinessValidator):
    proposition: Proposition

    def validate(self, *args, **kwargs):
        if not self.proposition.motif_refus_fac and not self.proposition.autre_motif_refus_fac:
            raise MotifRefusFacultaireNonSpecifieException


@attr.dataclass(frozen=True, slots=True)
class ShouldSpecifierInformationsAcceptationFacultaire(BusinessValidator):
    proposition: Proposition

    def validate(self, *args, **kwargs):
        if (
            self.proposition.avec_conditions_complementaires is None
            or self.proposition.avec_conditions_complementaires
            and not (
                self.proposition.conditions_complementaires_libres
                or self.proposition.conditions_complementaires_existantes
            )
            or self.proposition.avec_complements_formation is None
            or self.proposition.avec_complements_formation
            and not self.proposition.complements_formation
            or not self.proposition.nombre_annees_prevoir_programme
        ):
            raise InformationsAcceptationFacultaireNonSpecifieesException
