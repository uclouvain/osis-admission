# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPMinimaleFactory,
)
from admission.ddd.admission.domain.service.i_elements_confirmation import IElementsConfirmation
from admission.infrastructure.admission.doctorat.preparation.domain.service.in_memory.doctorat import (
    DoctoratInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator


class ElementsConfirmationInMemory(IElementsConfirmation):
    @classmethod
    def est_candidat_avec_etudes_secondaires_belges_francophones(cls, matricule: str) -> bool:
        return False

    @classmethod
    def get_elements_for_tests(cls, proposition=None, formation_translator=None, profil_translator=None):
        elements = cls.recuperer(
            proposition or PropositionAdmissionSC3DPMinimaleFactory(),
            formation_translator or DoctoratInMemoryTranslator(),
            profil_translator or ProfilCandidatInMemoryTranslator(),
        )
        return {
            element.nom: (f"{element.reponses[0]} {element.texte}" if element.reponses else element.texte)
            for element in elements
        }
