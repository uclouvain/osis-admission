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
from abc import abstractmethod

from admission.ddd.preparation.projet_doctoral.dtos import (
    CurriculumDTO,
    CoordonneesDTO,
    IdentificationDTO,
)
from osis_common.ddd import interface


class IProfilCandidatTranslator(interface.DomainService):
    CODES_LANGUES_CONNUES_REQUISES = ['FR', 'EN']

    NB_MAX_ANNEES_CV_REQUISES = 5

    @classmethod
    @abstractmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_coordonnees(cls, matricule: str) -> 'CoordonneesDTO':
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_langues_connues(cls, matricule: str) -> int:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_curriculum(cls, matricule: str) -> 'CurriculumDTO':
        raise NotImplementedError
