##############################################################################
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
##############################################################################
from django.utils.translation import ngettext

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import MaximumPropositionsAtteintException
from admission.ddd.admission.domain.validator.exceptions import NombrePropositionsSoumisesDepasseException
from osis_common.ddd import interface

MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_DOCTORALE = 1
MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_GENERALE = 2
MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_CONTINUE = 2
MAXIMUM_PROPOSITIONS_EN_COURS = 5


class IMaximumPropositionsAutorisees(interface.DomainService):
    @classmethod
    def nb_propositions_envoyees_formation_generale(cls, matricule: str) -> int:
        raise NotImplementedError

    @classmethod
    def nb_propositions_envoyees_formation_continue(cls, matricule: str) -> int:
        raise NotImplementedError

    @classmethod
    def nb_propositions_envoyees_formation_doctorale(cls, matricule: str) -> int:
        raise NotImplementedError

    @classmethod
    def nb_propositions_en_cours(cls, matricule: str) -> int:
        raise NotImplementedError

    @classmethod
    def verifier_nombre_propositions_envoyees_formation_generale(cls, matricule: str) -> None:
        if (
            cls.nb_propositions_envoyees_formation_generale(matricule)
            >= MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_GENERALE
        ):
            raise NombrePropositionsSoumisesDepasseException(
                ngettext(
                    'You cannot submit this admission for a general education as you already have submitted one.',
                    'You cannot submit this admission for a general education as '
                    'you already have submitted %(maximum_number)s of them.',
                    MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_GENERALE,
                )
                % {
                    'maximum_number': MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_GENERALE,
                }
            )

    @classmethod
    def verifier_nombre_propositions_envoyees_formation_continue(cls, matricule: str) -> None:
        if (
            cls.nb_propositions_envoyees_formation_continue(matricule)
            >= MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_CONTINUE
        ):
            raise NombrePropositionsSoumisesDepasseException(
                ngettext(
                    'You cannot submit this admission for a continuing education as you already have submitted one.',
                    'You cannot submit this admission for a continuing education as '
                    'you already have submitted %(maximum_number)s of them.',
                    MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_CONTINUE,
                )
                % {
                    'maximum_number': MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_CONTINUE,
                }
            )

    @classmethod
    def verifier_nombre_propositions_envoyees_formation_doctorale(cls, matricule: str) -> None:
        if (
            cls.nb_propositions_envoyees_formation_doctorale(matricule)
            >= MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_DOCTORALE
        ):
            raise NombrePropositionsSoumisesDepasseException(
                ngettext(
                    'You cannot submit this admission for a doctorate education as you already have submitted one.',
                    'You cannot submit this admission for a doctorate education as '
                    'you already have submitted %(maximum_number)s of them.',
                    MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_DOCTORALE,
                )
                % {
                    'maximum_number': MAXIMUM_PROPOSITIONS_ENVOYEES_FORMATION_DOCTORALE,
                }
            )

    @classmethod
    def verifier_nombre_propositions_en_cours(cls, matricule: str) -> None:
        if cls.nb_propositions_en_cours(matricule) >= MAXIMUM_PROPOSITIONS_EN_COURS:
            raise MaximumPropositionsAtteintException(MAXIMUM_PROPOSITIONS_EN_COURS)
