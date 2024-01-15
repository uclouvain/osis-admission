# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from abc import ABCMeta

from osis_common.ddd import interface


def formater_reference(reference: int, nom_campus_inscription: str, sigle_entite_gestion: str, annee: int) -> str:
    """Formater la référence d'une admission"""
    reference_formatee = '{:08}'.format(reference)
    reference_formatee = f'{reference_formatee[:4]}.{reference_formatee[4:]}'
    return f'{nom_campus_inscription[0]}-{sigle_entite_gestion}{annee % 100}-{reference_formatee}'


class IGlobalPropositionRepository(interface.AbstractRepository, metaclass=ABCMeta):
    @classmethod
    def recuperer_reference_suivante(cls) -> int:
        raise NotImplementedError
