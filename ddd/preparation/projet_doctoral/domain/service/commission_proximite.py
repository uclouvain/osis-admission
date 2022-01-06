##############################################################################
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
##############################################################################
from admission.ddd.preparation.projet_doctoral.domain.model._enums import (
    ChoixCommissionProximiteCDE,
    ChoixCommissionProximiteCDSS,
)
from admission.ddd.preparation.projet_doctoral.domain.model.doctorat import Doctorat
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    CommissionProximiteInconsistantException,
)
from osis_common.ddd import interface


class CommissionProximite(interface.DomainService):
    @classmethod
    def verifier(cls, doctorat: "Doctorat", commission_proximite: str) -> None:
        if doctorat.est_entite_CDE() and (
            not commission_proximite
            or commission_proximite not in ChoixCommissionProximiteCDE.get_names()
        ):
            raise CommissionProximiteInconsistantException()
        if doctorat.est_entite_CDSS() and (
            not commission_proximite
            or commission_proximite not in ChoixCommissionProximiteCDSS.get_names()
        ):
            raise CommissionProximiteInconsistantException()
        if (
            not doctorat.est_entite_CDE()
            and not doctorat.est_entite_CDSS()
            and commission_proximite
        ):
            raise CommissionProximiteInconsistantException()
