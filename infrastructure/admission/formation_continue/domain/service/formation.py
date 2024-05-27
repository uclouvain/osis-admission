##############################################################################
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
##############################################################################
import unicodedata
import uuid
from typing import List, Optional, Dict

from django.conf import settings
from django.utils.translation import get_language

from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.domain.model._campus import Campus
from admission.ddd.admission.domain.model.formation import Formation, FormationIdentity
from admission.ddd.admission.dtos.campus import CampusDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.domain.service.i_formation import IFormationContinueTranslator
from admission.ddd.admission.formation_continue.domain.validator.exceptions import FormationNonTrouveeException
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.campus import Campus as CampusDBModel
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.education_group_types import TrainingType
from ddd.logic.formation_catalogue.commands import SearchFormationsCommand, RecupererFormationQuery
from ddd.logic.formation_catalogue.domain.validators.exceptions import TrainingNotFoundException
from ddd.logic.formation_catalogue.dtos.training import TrainingDto
from ddd.logic.formation_catalogue.formation_continue.commands import RecupererInformationsSpecifiquesQuery
from ddd.logic.formation_catalogue.formation_continue.domain.validator.exceptions import (
    InformationsSpecifiquesNonTrouveesException,
)
from ddd.logic.formation_catalogue.formation_continue.dtos.informations_specifiques import InformationsSpecifiquesDTO
from ddd.logic.shared_kernel.academic_year.commands import SearchAcademicYearCommand
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear
from ddd.logic.shared_kernel.campus.commands import GetCampusQuery, SearchUclouvainCampusesQuery
from ddd.logic.shared_kernel.campus.dtos import UclouvainCampusDTO


class FormationContinueTranslator(IFormationContinueTranslator):
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
    def _build_dto(
        cls,
        dto: 'TrainingDto',
        campuses_by_uuid: Dict[str, UclouvainCampusDTO] = None,
        academic_years_by_year: Dict[int, AcademicYear] = None,
    ) -> 'FormationDTO':
        """
        Build a FormationDTO from a TrainingDto
        :param dto: the input dto
        :param campuses_by_uuid: dictionary associating the uuid of the campus and its dto. If not specified, the
        search will be done in this method.
        :param academic_years_by_year: dictionary associating the year of the academic year and its dto. If not
        specified, the search will be done in this method.
        :return: the output dto
        """
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

        return FormationDTO(
            sigle=dto.acronym,
            annee=dto.year,
            date_debut=academic_year.start_date,
            intitule=dto.title_fr if get_language() == settings.LANGUAGE_CODE_FR else dto.title_en,
            intitule_fr=dto.title_fr,
            intitule_en=dto.title_en,
            campus=CampusDTO(
                uuid=uuid.UUID(str(campus.uuid)),
                nom=campus.name,
                code_postal=campus.postal_code,
                ville=campus.city,
                pays_iso_code=campus.country_iso_code,
                nom_pays=campus.country_name,
                rue=campus.street,
                numero_rue=campus.street_number,
                boite_postale=campus.postal_box,
                localisation=campus.location,
                email_inscription_sic=campus.sic_enrollment_email,
            )
            if campus is not None
            else None,
            type=dto.type,
            code_domaine=dto.main_domain_code or '',
            campus_inscription=CampusDTO(
                uuid=uuid.UUID(str(campus_inscription.uuid)),
                nom=campus_inscription.name,
                code_postal=campus_inscription.postal_code,
                ville=campus_inscription.city,
                pays_iso_code=campus_inscription.country_iso_code,
                nom_pays=campus_inscription.country_name,
                rue=campus_inscription.street,
                numero_rue=campus_inscription.street_number,
                boite_postale=campus_inscription.postal_box,
                localisation=campus_inscription.location,
                email_inscription_sic=campus_inscription.sic_enrollment_email,
            )
            if campus_inscription is not None
            else None,
            sigle_entite_gestion=dto.management_entity_acronym or '',
            code=dto.code,
            credits=dto.credits,
        )

    @classmethod
    def get_dto(cls, sigle: str, annee: int) -> 'FormationDTO':  # pragma: no cover
        from infrastructure.messages_bus import message_bus_instance

        try:
            training_dto: TrainingDto = message_bus_instance.invoke(
                RecupererFormationQuery(sigle_formation=sigle, annee_formation=annee)
            )
            return cls._build_dto(training_dto)
        except TrainingNotFoundException:
            raise FormationNonTrouveeException

    @classmethod
    def get(cls, entity_id: FormationIdentity) -> 'Formation':
        from infrastructure.messages_bus import message_bus_instance

        try:
            dto: TrainingDto = message_bus_instance.invoke(
                RecupererFormationQuery(
                    sigle_formation=entity_id.sigle,
                    annee_formation=entity_id.annee,
                )
            )
            try:
                campus: Optional['UclouvainCampusDTO'] = message_bus_instance.invoke(
                    GetCampusQuery(uuid=dto.main_teaching_campus_uuid)
                )
            except CampusDBModel.DoesNotExist:
                campus = None

            return Formation(
                entity_id=FormationIdentity(sigle=dto.acronym, annee=dto.year),
                type=TrainingType[dto.type],
                code_domaine=dto.main_domain_code or '',
                campus=Campus(
                    nom=campus.name,
                    code_postal=campus.postal_code,
                    ville=campus.city,
                    pays_iso_code=campus.country_iso_code,
                    nom_pays=campus.country_name,
                    rue=campus.street,
                    numero_rue=campus.street_number,
                    localisation=campus.location,
                    email_inscription_sic=campus.sic_enrollment_email,
                )
                if campus is not None
                else None,
            )

        except TrainingNotFoundException:
            raise FormationNonTrouveeException

    @classmethod
    def search(
        cls,
        annee: Optional[int],
        terme_de_recherche: Optional[str],
        campus: Optional[str],
    ) -> List['FormationDTO']:
        from infrastructure.messages_bus import message_bus_instance

        if not annee:
            return []

        dtos: List[TrainingDto] = message_bus_instance.invoke(
            SearchFormationsCommand(
                annee=annee,
                campus=campus,
                est_inscriptible=True,
                uclouvain_est_institution_reference=True,
                inscription_web=True,
                statut=ActiveStatusEnum.ACTIVE.name,
                terme_de_recherche=terme_de_recherche,
                types=AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(
                    TypeFormation.FORMATION_CONTINUE.name
                ),
            )
        )

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
                key=lambda formation: f'{unicodedata.normalize("NFKD", formation.intitule)}'
                + (' {formation.campus.nom}' if formation.campus else ''),
            )
        )

    @classmethod
    def verifier_existence(cls, sigle: str, annee: int) -> bool:  # pragma: no cover
        from infrastructure.messages_bus import message_bus_instance

        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(
                sigles_annees=[(sigle, annee)],
                est_inscriptible=True,
                uclouvain_est_institution_reference=True,
                inscription_web=True,
                statut=ActiveStatusEnum.ACTIVE.name,
                type=AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(
                    TypeFormation.FORMATION_CONTINUE.name
                ),
            )
        )
        return bool(dtos)

    @classmethod
    def get_informations_specifiques_dto(cls, entity_id: FormationIdentity) -> Optional[InformationsSpecifiquesDTO]:
        from infrastructure.messages_bus import message_bus_instance

        try:
            return message_bus_instance.invoke(
                RecupererInformationsSpecifiquesQuery(
                    sigle_formation=entity_id.sigle,
                    annee=entity_id.annee,
                )
            )
        except InformationsSpecifiquesNonTrouveesException:
            pass
