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
from typing import Optional

import attr

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    MembreSoitInterneSoitExterneException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldMembreEtreInterneOuExterne(BusinessValidator):
    matricule: Optional[str]
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]

    def validate(self, *args, **kwargs):
        champs_externes = ['prenom', 'nom', 'email', 'institution', 'ville', 'pays', 'langue']
        if (
            # Can't be internal and have external data
            self.matricule
            and any(getattr(self, champ) for champ in champs_externes)
            # Can't be a partially defined external
            or not self.matricule
            and not all(getattr(self, champ) for champ in champs_externes)
        ):
            raise MembreSoitInterneSoitExterneException
