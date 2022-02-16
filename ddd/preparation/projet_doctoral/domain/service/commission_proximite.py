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
from typing import Optional

from admission.ddd.preparation.projet_doctoral.domain.model._enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.ddd.preparation.projet_doctoral.domain.model.doctorat import Doctorat
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    CommissionProximiteInconsistantException,
)
from osis_common.ddd import interface


class CommissionProximite(interface.DomainService):
    @classmethod
    def verifier(cls, doctorat: "Doctorat", commission_proximite: Optional[str]) -> None:
        if (doctorat.est_entite_CDE() or doctorat.est_entite_CLSM()) and (
            not commission_proximite
            or commission_proximite not in ChoixCommissionProximiteCDEouCLSM.get_names()
        ):
            raise CommissionProximiteInconsistantException()
        elif doctorat.est_entite_CDSS() and (
            not commission_proximite
            or commission_proximite not in ChoixCommissionProximiteCDSS.get_names()
        ):
            raise CommissionProximiteInconsistantException()
        elif doctorat.est_domaine_des_sciences() and (
            not commission_proximite or commission_proximite not in ChoixSousDomaineSciences.get_names()
        ):
            raise CommissionProximiteInconsistantException()
        elif (
            not doctorat.est_entite_CDE()
            and not doctorat.est_entite_CDSS()
            and not doctorat.est_entite_CLSM()
            and not doctorat.est_domaine_des_sciences()
            and commission_proximite
        ):
            raise CommissionProximiteInconsistantException()
