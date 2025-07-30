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
from abc import abstractmethod
from typing import List, Optional

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import DoctoratFormation
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratFormationDTO
from admission.ddd.admission.shared_kernel.domain.service.i_formation_translator import IFormationTranslator


class IDoctoratTranslator(IFormationTranslator):
    @classmethod
    @abstractmethod
    def get(cls, sigle: str, annee: int) -> DoctoratFormation:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_dto(cls, sigle: str, annee: int) -> DoctoratFormationDTO:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def search(
        cls,
        sigle_secteur_entite_gestion: str,
        annee: Optional[int] = None,
        campus: Optional[str] = '',
        terme_de_recherche: Optional[str] = '',
    ) -> List['DoctoratFormationDTO']:
        raise NotImplementedError
