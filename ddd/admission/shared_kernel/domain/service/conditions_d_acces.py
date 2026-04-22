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
from epc.models.enums.condition_acces import ConditionAcces
from osis_common.ddd import interface

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition as PropositionDoctorat
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGeneral
from admission.ddd.admission.shared_kernel.domain.model.enums.condition_acces import ErreurConditionAcces
from ddd.logic.condition_acces.domain.service.calcul_condition_acces import ConditionAccesInsuffisant, \
    ConditionAccesIncomplet


class ConditionDAcces(interface.DomainService):
    @classmethod
    def calculer_condition_d_acces(
        cls,
        proposition: PropositionDoctorat | PropositionGeneral,
        calcul_condition_acces_translator: 'ICalculConditionAccesTranslator',
    ):
        try:
            condition_acces = calcul_condition_acces_translator.calculer_condition_d_acces(proposition)
            if condition_acces is None:
                proposition.specifier_condition_acces(condition_acces=None, millesime=None)
            else:
                proposition.specifier_condition_acces(condition_acces=ConditionAcces[condition_acces.condition],
                                                      millesime=condition_acces.millesime)
        except ConditionAccesInsuffisant:
            proposition.specifier_erreur_condition_acces(ErreurConditionAcces.INSUFFISANT)
        except ConditionAccesIncomplet:
            proposition.specifier_erreur_condition_acces(ErreurConditionAcces.INCOMPLET)
