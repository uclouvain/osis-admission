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
from typing import List, Optional

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
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.education_group_types import TrainingType
from ddd.logic.formation_catalogue.commands import SearchFormationsCommand
from ddd.logic.formation_catalogue.dtos.training import TrainingDto
from ddd.logic.shared_kernel.academic_year.commands import SearchAcademicYearCommand
from ddd.logic.shared_kernel.campus.commands import GetCampusQuery
from ddd.logic.shared_kernel.campus.dtos import UclouvainCampusDTO


class FormationContinueTranslator(IFormationContinueTranslator):
    @classmethod
    def _build_dto(cls, dto: 'TrainingDto') -> 'FormationDTO':
        from infrastructure.messages_bus import message_bus_instance

        academic_year = message_bus_instance.invoke(SearchAcademicYearCommand(year=dto.year, to_year=dto.year))[0]

        try:
            campus: 'UclouvainCampusDTO' = message_bus_instance.invoke(
                GetCampusQuery(uuid=dto.main_teaching_campus_uuid)
            )
        except Exception:
            campus = None
        try:
            campus_inscription: 'UclouvainCampusDTO' = message_bus_instance.invoke(
                GetCampusQuery(uuid=dto.enrollment_campus_uuid)
            )
        except Exception:
            campus_inscription = None

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
                email=campus.sic_enrollment_email,
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
                email=campus_inscription.email,
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

        dtos = message_bus_instance.invoke(SearchFormationsCommand(sigles_annees=[(sigle, annee)]))

        if dtos:
            return cls._build_dto(dtos[0])

        raise FormationNonTrouveeException

    @classmethod
    def get(cls, entity_id: FormationIdentity) -> 'Formation':
        from infrastructure.messages_bus import message_bus_instance

        dtos = message_bus_instance.invoke(
            SearchFormationsCommand(
                sigles_annees=[(entity_id.sigle, entity_id.annee)],
                types=AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(
                    TypeFormation.FORMATION_CONTINUE.name
                ),
            )
        )

        if dtos:
            dto: TrainingDto = dtos[0]

            try:
                campus: 'UclouvainCampusDTO' = message_bus_instance.invoke(
                    GetCampusQuery(uuid=dto.main_teaching_campus_uuid)
                )
            except Exception:
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
                    email=campus.sic_enrollment_email,
                )
                if campus is not None
                else None,
            )

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

        dtos = message_bus_instance.invoke(
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

        results = [cls._build_dto(dto) for dto in dtos]
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
