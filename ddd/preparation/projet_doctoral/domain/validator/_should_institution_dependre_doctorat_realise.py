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
from typing import Optional

import attr

from base.ddd.utils.business_validator import BusinessValidator
from admission.ddd.preparation.projet_doctoral.domain.model._experience_precedente_recherche import ChoixDoctoratDejaRealise
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import InstitutionInconsistanteException


@attr.s(frozen=True, slots=True)
class ShouldInstitutionDependreDoctoratRealise(BusinessValidator):
    doctorat_deja_realise = attr.ib(type=str, default=ChoixDoctoratDejaRealise.NO.name)
    institution = attr.ib(type=Optional[str], default='')

    def validate(self, *args, **kwargs):
        # TODO :: unit tests
        if ChoixDoctoratDejaRealise[self.doctorat_deja_realise] == ChoixDoctoratDejaRealise.NO and self.institution:
            raise InstitutionInconsistanteException()
        if ChoixDoctoratDejaRealise[self.doctorat_deja_realise] != ChoixDoctoratDejaRealise.NO and not self.institution:
            raise InstitutionInconsistanteException()
