# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.shared_kernel.domain.model.formation import Formation
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    BoursesEtudesNonRenseignees,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldRenseignerBoursesEtudesSelonFormation(BusinessValidator):
    formation: Formation
    proposition: 'Proposition'

    def validate(self, *args, **kwargs):
        if not self.formation.est_formation_avec_bourse:
            return

        if (
            self.proposition.avec_bourse_erasmus_mundus is None
            or self.proposition.avec_bourse_erasmus_mundus
            and not self.proposition.bourse_erasmus_mundus_id
            or self.proposition.avec_bourse_internationale is None
            or self.proposition.avec_bourse_internationale
            and not self.proposition.bourse_internationale_id
            or self.proposition.avec_bourse_double_diplome is None
            or self.proposition.avec_bourse_double_diplome
            and not self.proposition.bourse_double_diplome_id
        ):
            raise BoursesEtudesNonRenseignees
