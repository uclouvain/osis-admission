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

from typing import List

from admission.ddd.admission.shared_kernel.email_destinataire.domain.validator.exceptions import \
    InformationsDestinatairePasTrouvee
from admission.ddd.admission.shared_kernel.email_destinataire.dtos.destinataire import InformationsDestinataireDTO
from admission.ddd.admission.shared_kernel.email_destinataire.repository.i_email_destinataire import \
    IEmailDestinataireRepository
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository


class EmailDestinataireInMemoryRepository(InMemoryGenericRepository, IEmailDestinataireRepository):
    _destinataires_dto: List['InformationsDestinataireDTO'] = [
        InformationsDestinataireDTO(
            annee=2022,
            sigle_formation='DROI1BA',
            pour_premiere_annee=False,
            en_tete='Prénom nom',
            email='test@test.be',
        ),
        InformationsDestinataireDTO(
            annee=2022,
            sigle_formation='DROI1BA',
            pour_premiere_annee=False,
            en_tete='Prénom nom',
            email='test@test.be',
        ),
    ]

    @classmethod
    def get_informations_destinataire_dto(
        cls,
        sigle_programme: str,
        annee: int,
        pour_premiere_annee: bool,
    ) -> 'InformationsDestinataireDTO':
        try:
            return next(
                dto
                for dto in cls._destinataires_dto
                if dto.sigle_formation == sigle_programme
                and dto.annee == annee
                and dto.pour_premiere_annee == pour_premiere_annee
            )
        except StopIteration as e:
            raise InformationsDestinatairePasTrouvee from e
