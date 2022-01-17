# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial

from admission.ddd.preparation.projet_doctoral.domain.model.groupe_de_supervision import GroupeDeSupervision
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import Proposition
from admission.ddd.preparation.projet_doctoral.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.preparation.projet_doctoral.domain.service.verifier_cotutelle import CotutellePossedePromoteurExterne
from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from osis_common.ddd import interface


class VerifierProjetDoctoral(interface.DomainService):
    @classmethod
    def verifier(
            cls,
            proposition_candidat: Proposition,
            groupe_de_supervision: GroupeDeSupervision,
            promoteur_translator: IPromoteurTranslator,
    ) -> None:
        execute_functions_and_aggregate_exceptions(
            groupe_de_supervision.verifier_cotutelle,
            partial(CotutellePossedePromoteurExterne.verifier, groupe_de_supervision, promoteur_translator),
            proposition_candidat.verifier_projet_doctoral,
            groupe_de_supervision.verifier_signataires,
        )
