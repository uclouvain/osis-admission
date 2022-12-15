##############################################################################
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
##############################################################################
import unicodedata
from typing import List, Optional

from django.conf import settings
from django.utils.translation import get_language

from admission.ddd.admission.domain.model.formation import Formation, FormationIdentity
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_generale.domain.service.i_formation import IFormationGeneraleTranslator
from admission.ddd.admission.formation_generale.domain.validator.exceptions import FormationNonTrouveeException
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.enums.education_group_types import TrainingType
from ddd.logic.formation_catalogue.commands import SearchFormationsCommand
from ddd.logic.formation_catalogue.dtos.training import TrainingDto


class FormationGeneraleTranslator(IFormationGeneraleTranslator):
    @classmethod
    def _build_dto(cls, dto: 'TrainingDto') -> 'FormationDTO':
        return FormationDTO(
            sigle=dto.acronym,
            annee=dto.year,
            intitule=dto.title_fr if get_language() == settings.LANGUAGE_CODE else dto.title_en,
            campus=dto.main_teaching_campus_name or '',
            type=dto.type,
        )

    @classmethod
    def get_dto(cls, sigle: str, annee: int) -> 'FormationDTO':  # pragma: no cover
        from infrastructure.messages_bus import message_bus_instance

        dtos = message_bus_instance.invoke(SearchFormationsCommand(sigle=sigle, annee=annee))

        if dtos:
            return cls._build_dto(dtos[0])

        raise FormationNonTrouveeException

    @classmethod
    def get(cls, entity_id: FormationIdentity) -> 'Formation':
        from infrastructure.messages_bus import message_bus_instance

        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(
                sigle=entity_id.sigle,
                annee=entity_id.annee,
                types=list(AnneeInscriptionFormationTranslator.GENERAL_EDUCATION_TYPES),
            )
        )

        if dtos:
            dto: TrainingDto = dtos[0]

            return Formation(
                entity_id=FormationIdentity(sigle=dto.acronym, annee=dto.year),
                type=TrainingType[dto.type],
            )

        raise FormationNonTrouveeException

    @classmethod
    def search(
        cls,
        type: str,
        annee: Optional[int],
        intitule: Optional[str],
        campus: Optional[str],
    ) -> List['FormationDTO']:
        from infrastructure.messages_bus import message_bus_instance

        if not annee:
            return []

        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(
                annee=annee,
                campus=campus,
                est_inscriptible=True,
                intitule=intitule,
                types=AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(
                    type,
                    list(AnneeInscriptionFormationTranslator.GENERAL_EDUCATION_TYPES),
                ),
            )
        )

        results = [cls._build_dto(dto) for dto in dtos]
        return list(
            sorted(
                results,
                key=lambda formation: f'{unicodedata.normalize("NFKD", formation.intitule)} {formation.campus}',
            )
        )

    @classmethod
    def verifier_existence(cls, sigle: str, annee: int) -> bool:
        from infrastructure.messages_bus import message_bus_instance

        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(
                sigle=sigle,
                annee=annee,
                est_inscriptible=True,
                types=list(AnneeInscriptionFormationTranslator.GENERAL_EDUCATION_TYPES),
            )
        )
        return bool(dtos)
