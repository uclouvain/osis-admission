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

from admission.ddd.preparation.projet_doctoral.domain.model._cotutelle import Cotutelle, pas_de_cotutelle
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import CotutelleNonCompleteException
from base.ddd.utils.business_validator import BusinessValidator


@attr.s(frozen=True, slots=True)
class ShouldCotutelleEtreComplete(BusinessValidator):
    cotutelle = attr.ib(type="Cotutelle")  # type: Cotutelle

    def validate(self, *args, **kwargs):
        champs_obligatoires = [
            "motivation",
            "institution",
            "demande_ouverture",
        ]
        if (
                self.cotutelle is None
                or (
                    self.cotutelle != pas_de_cotutelle
                    and not all(
                        [getattr(self.cotutelle, champ_obligatoire) for champ_obligatoire in champs_obligatoires]
                    )
                )
        ):
            raise CotutelleNonCompleteException
