
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

from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import \
    GroupeSupervisionCompletPourMembresCAException
from base.ddd.utils.business_validator import BusinessValidator
from admission.ddd.preparation.projet_doctoral.business_types import *


@attr.s(frozen=True, slots=True)
class ShouldGroupeDeSupervisionNonCompletPourMembreCA(BusinessValidator):
    groupe_de_supervision = attr.ib(type='GroupeDeSupervision')  # type: GroupeDeSupervision
    NOMBRE_MAX_MEMBRES_CA = 3

    def validate(self, *args, **kwargs):
        if len(self.groupe_de_supervision.signatures_membres_CA) >= self.NOMBRE_MAX_MEMBRES_CA:
            raise GroupeSupervisionCompletPourMembresCAException
