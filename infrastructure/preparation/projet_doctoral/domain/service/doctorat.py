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
from typing import List

from base.models.enums.education_group_types import TrainingType
from admission.ddd.preparation.projet_doctoral.domain.model.doctorat import Doctorat, DoctoratIdentity
from admission.ddd.preparation.projet_doctoral.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import DoctoratDTO
from ddd.logic.formation_catalogue.commands import SearchFormationsCommand
from ddd.logic.formation_catalogue.dtos import TrainingDto
from ddd.logic.learning_unit.domain.model.responsible_entity import UCLEntityIdentity  # FIXME reuse from shared_kernel


class DoctoratTranslator(IDoctoratTranslator):
    @classmethod
    def get_dto(cls, sigle: str, annee: int) -> DoctoratDTO:
        from infrastructure.messages_bus import message_bus_instance
        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(sigle=sigle, annee=annee, type=TrainingType.PHD.name)
        )
        if dtos:
            dto = dtos[0]  # type: TrainingDto
            return DoctoratDTO(
                sigle=dto.acronym,
                annee=dto.year,
                intitule_fr=dto.title_fr,
                intitule_en=dto.title_en,
                sigle_entite_gestion=dto.management_entity_acronym,
            )
        raise DoctoratNonTrouveException()

    @classmethod
    def get(cls, sigle: str, annee: int) -> Doctorat:
        from infrastructure.messages_bus import message_bus_instance
        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(sigle=sigle, annee=annee, type=TrainingType.PHD.name)
        )
        if dtos:
            dto = dtos[0]  # type: TrainingDto
            return Doctorat(
                entity_id=DoctoratIdentity(sigle=dto.acronym, annee=dto.year),
                entite_ucl_id=UCLEntityIdentity(code=dto.management_entity_acronym),
            )
        raise DoctoratNonTrouveException()

    @classmethod
    def search(cls, sigle_entite_gestion: str, annee: int) -> List['DoctoratDTO']:
        from infrastructure.messages_bus import message_bus_instance
        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(
                annee=annee,
                sigle_entite_gestion=sigle_entite_gestion,
                inclure_entites_gestion_subordonnees=True,
                type=TrainingType.PHD.name,
            )
        )
        return [
            DoctoratDTO(
                sigle=dto.acronym,
                annee=dto.year,
                intitule_fr=dto.title_fr,
                intitule_en=dto.title_en,
                sigle_entite_gestion=dto.management_entity_acronym,
            ) for dto in dtos
        ]
