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

from admission.ddd.parcours_doctoral.jury.domain.model.enums import TitreMembre
from admission.ddd.parcours_doctoral.jury.validator.exceptions import NonDocteurSansJustificationException
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldNonDocteurAvoirJustification(BusinessValidator):
    membre: 'MembreJury'

    def validate(self, *args, **kwargs):
        if self.membre.titre == TitreMembre.NON_DOCTEUR.name and not self.membre.justification_non_docteur:
            raise NonDocteurSansJustificationException
