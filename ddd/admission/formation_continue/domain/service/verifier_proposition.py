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

from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition
from admission.ddd.admission.formation_continue.domain.service.i_formation import IFormationContinueTranslator
from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from osis_common.ddd import interface


class VerifierProposition(interface.DomainService):
    @classmethod
    def verifier(
        cls,
        proposition_candidat: Proposition,
        formation_translator: IFormationContinueTranslator,
        titres_acces: ITitresAcces,
    ) -> None:
        execute_functions_and_aggregate_exceptions(
            # TODO check other tabs
            partial(
                titres_acces.verifier,
                proposition_candidat.matricule_candidat,
                formation_translator.get(proposition_candidat.formation_id).type,
            ),
        )
