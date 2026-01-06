# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.shared_kernel.domain.model.titre_acces_selectionnable import TitreAccesSelectionnable
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import (
    TitresAccesEtreExperiencesNonAcademiquesOuUneExperienceAcademiqueException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldTitresAccesEtreExperiencesNonAcademiquesOuUneExperienceAcademique(BusinessValidator):
    titre_acces_modifie: TitreAccesSelectionnable
    titres_acces_deja_selectionnes: list[TitreAccesSelectionnable]

    def validate(self, *args, **kwargs):
        if self.titre_acces_modifie.selectionne and (
            (
                self.titre_acces_modifie.entity_id.type_titre.est_non_academique()
                and any(titre.entity_id.type_titre.est_academique() for titre in self.titres_acces_deja_selectionnes)
            )
            or (self.titre_acces_modifie.entity_id.type_titre.est_academique() and self.titres_acces_deja_selectionnes)
        ):
            raise TitresAccesEtreExperiencesNonAcademiquesOuUneExperienceAcademiqueException
