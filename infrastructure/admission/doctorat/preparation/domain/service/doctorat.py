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
import unicodedata
from typing import List, Optional, Dict

from django.conf import settings
from django.utils.translation import get_language

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import Doctorat
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratDTO
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.dtos.campus import CampusDTO
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.education_group_types import TrainingType
from ddd.logic.formation_catalogue.commands import SearchFormationsCommand
from ddd.logic.formation_catalogue.dtos.training import TrainingDto
from ddd.logic.learning_unit.domain.model.responsible_entity import UCLEntityIdentity  # FIXME reuse from shared_kernel
from ddd.logic.shared_kernel.academic_year.commands import SearchAcademicYearCommand
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear
from ddd.logic.shared_kernel.campus.commands import SearchUclouvainCampusesQuery
from ddd.logic.shared_kernel.campus.dtos import UclouvainCampusDTO


class DoctoratTranslator(IDoctoratTranslator):
    @classmethod
    def _build_dto(
        cls,
        dto: 'TrainingDto',
        campuses_by_uuid: Dict[str, UclouvainCampusDTO] = None,
        academic_years_by_year: Dict[int, AcademicYear] = None,
    ) -> 'DoctoratDTO':
        # Load the academic year if not already loaded
        if not academic_years_by_year:
            academic_years_by_year = cls._get_academic_years_by_year(years=[dto.year])

        academic_year = academic_years_by_year[dto.year]

        # Load the campuses if not already loaded
        if not campuses_by_uuid:
            campuses_uuids = []

            if dto.main_teaching_campus_uuid:
                campuses_uuids.append(dto.main_teaching_campus_uuid)

            if dto.enrollment_campus_uuid:
                campuses_uuids.append(dto.enrollment_campus_uuid)

            campuses_by_uuid = cls._get_campuses_by_uuid(campuses_uuids)

        campus = (
            campuses_by_uuid[dto.main_teaching_campus_uuid]
            if dto.main_teaching_campus_uuid in campuses_by_uuid
            else None
        )

        campus_inscription = (
            campuses_by_uuid[dto.enrollment_campus_uuid] if dto.enrollment_campus_uuid in campuses_by_uuid else None
        )

        return DoctoratDTO(
            sigle=dto.acronym,
            code=dto.code,
            annee=dto.year,
            date_debut=academic_year.start_date,
            intitule=dto.title_fr if get_language() == settings.LANGUAGE_CODE_FR else dto.title_en,
            intitule_fr=dto.title_fr,
            intitule_en=dto.title_en,
            sigle_entite_gestion=dto.management_entity_acronym,
            campus_inscription=CampusDTO.from_uclouvain_campus_dto(campus_inscription),
            campus=CampusDTO.from_uclouvain_campus_dto(campus),
            type=dto.type,
            credits=dto.credits,
        )

    @classmethod
    def _get_campuses_by_uuid(cls, campuses_uuids: List[str]) -> Dict[str, UclouvainCampusDTO]:
        """
        Get a dictionary associating the uuid of the campus and its information.
        :param campuses_uuids: a list of the uuids of the campuses
        :return: a dictionary associating the uuid of the campus and its dto
        """
        from infrastructure.messages_bus import message_bus_instance

        campuses: List[UclouvainCampusDTO] = (
            message_bus_instance.invoke(SearchUclouvainCampusesQuery(uuids=campuses_uuids)) if campuses_uuids else {}
        )

        return {campus.uuid: campus for campus in campuses}

    @classmethod
    def _get_academic_years_by_year(cls, years: List[int]) -> Dict[int, AcademicYear]:
        """
        Get a dictionary associating the year of the academic year and its information.
        :param years: a list of the years
        :return: a dictionary associating the year of the academic year and its dto
        """
        from infrastructure.messages_bus import message_bus_instance

        academic_years: List[AcademicYear] = (
            message_bus_instance.invoke(SearchAcademicYearCommand(year=min(years), to_year=max(years))) if years else []
        )

        return {academic_year.year: academic_year for academic_year in academic_years}

    @classmethod
    def get_dto(cls, sigle: str, annee: int) -> 'DoctoratDTO':  # pragma: no cover
        from infrastructure.messages_bus import message_bus_instance

        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(sigles_annees=[(sigle, annee)], type=TrainingType.PHD.name)
        )
        if dtos:
            return cls._build_dto(dtos[0])
        raise DoctoratNonTrouveException()

    @classmethod
    def get(cls, sigle: str, annee: int) -> 'Doctorat':
        from infrastructure.messages_bus import message_bus_instance

        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(sigles_annees=[(sigle, annee)], type=TrainingType.PHD.name)
        )
        if dtos:
            dto: TrainingDto = dtos[0]
            return Doctorat(
                entity_id=FormationIdentity(sigle=dto.acronym, annee=dto.year),
                entite_ucl_id=UCLEntityIdentity(code=dto.management_entity_acronym),
                type=TrainingType[dto.type],
            )
        raise DoctoratNonTrouveException()

    @classmethod
    def search(
        cls,
        sigle_secteur_entite_gestion: str,
        annee: Optional[int] = None,
        campus: Optional[str] = '',
        terme_de_recherche: Optional[str] = '',
    ) -> List['DoctoratDTO']:
        from infrastructure.messages_bus import message_bus_instance

        if not annee:
            return []

        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(
                annee=annee,
                sigle_entite_gestion=sigle_secteur_entite_gestion,
                inclure_entites_gestion_subordonnees=True,
                type=TrainingType.PHD.name,
                campus=campus,
                terme_de_recherche=terme_de_recherche,
                est_inscriptible=True,
                uclouvain_est_institution_reference=True,
                inscription_web=True,
                statut=ActiveStatusEnum.ACTIVE.name,
            )
        )

        # Load the academic years and the campuses data in bulk
        academic_years = set()
        campuses_uuids = set()

        for dto in dtos:
            academic_years.add(dto.year)

            if dto.enrollment_campus_uuid:
                campuses_uuids.add(dto.enrollment_campus_uuid)
            if dto.main_teaching_campus_uuid:
                campuses_uuids.add(dto.main_teaching_campus_uuid)

        academic_years_by_year = cls._get_academic_years_by_year(list(academic_years))
        campuses_by_uuid = cls._get_campuses_by_uuid(list(campuses_uuids))

        results = [
            cls._build_dto(
                dto,
                campuses_by_uuid=campuses_by_uuid,
                academic_years_by_year=academic_years_by_year,
            )
            for dto in dtos
        ]

        return list(
            sorted(
                results,
                key=lambda formation: f'{unicodedata.normalize("NFKD", formation.intitule)} {formation.campus}',
            )
        )

    @classmethod
    def verifier_existence(cls, sigle: str, annee: int) -> bool:  # pragma: no cover
        from infrastructure.messages_bus import message_bus_instance

        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(
                sigles_annees=[(sigle, annee)],
                type=TrainingType.PHD.name,
                est_inscriptible=True,
                uclouvain_est_institution_reference=True,
                inscription_web=True,
                statut=ActiveStatusEnum.ACTIVE.name,
            )
        )
        return bool(dtos)
