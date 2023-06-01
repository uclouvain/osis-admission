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
from typing import List

from django.db.models import Prefetch

from admission.contrib.models.jury import Verificateur as VerificateurORM
from admission.ddd.parcours_doctoral.jury.domain.model.verificateurs import Verificateur, VerificateurIdentity
from admission.ddd.parcours_doctoral.jury.dtos.verificateur import VerificateurDTO
from admission.ddd.parcours_doctoral.jury.repository.i_verificateur import IVerificateurRepository
from base.models.entity_version import find_all_current_entities_version, EntityVersion
from base.models.enums.entity_type import INSTITUTE
from ddd.logic.learning_unit.domain.model.responsible_entity import UCLEntityIdentity

SECTORS_ACRONYMS = ['SST', 'SSH']


class VerificateurRepository(IVerificateurRepository):
    @classmethod
    def get_list(cls) -> List['Verificateur']:  # type: ignore[override]
        queryset = (
            VerificateurORM.objects.all()
            .select_related('person')
            .prefetch_related(
                Prefetch(
                    'entity__entityversion',
                    queryset=EntityVersion.objects.select_related('parent__entityversion')
                )
            )
        )
        verificateurs = [
            Verificateur(
                entity_id=VerificateurIdentity(code=verificateur.entity.most_recent_acronym),
                entite_ucl_id=UCLEntityIdentity(code=verificateur.entity.most_recent_acronym),
                sector=verificateur.entity.most_recent_entity_version.parent.most_recent_acronym,
                matricule=verificateur.global_id,
            ) for verificateur in queryset
        ]

        # Add institutes without a verificateur yet
        codes = {verificateur.code for verificateur in verificateurs}
        for sector in SECTORS_ACRONYMS:
            try:
                sector = find_all_current_entities_version().select_related('entity').get(acronym=sector)
            except EntityVersion.DoesNotExist:
                continue
            institutes = sector.find_direct_children().filter(entity_type=INSTITUTE)
            for institute in institutes:
                if institute.acronym not in codes:
                    codes.add(institute.acronym)
                    verificateurs.append(
                        Verificateur(
                            entity_id=VerificateurIdentity(code=institute.acronym),
                            entite_ucl_id=UCLEntityIdentity(code=institute.acronym),
                            sector=sector,
                            matricule=None,
                        )
                    )
        return verificateurs

    @classmethod
    def get_list_dto(cls) -> List['VerificateurDTO']:
        return [
            cls._load_verificateur_dto(verificateur)
            for verificateur in cls.get_list()
        ]

    @classmethod
    def save_list(cls, entities: List['Verificateur']) -> List['VerificateurIdentity']:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def _load_verificateur_dto(cls, verificateur: Verificateur) -> VerificateurDTO:
        return VerificateurDTO(
            code=str(verificateur.entity_id.code),
            entite_ucl_id=str(verificateur.entite_ucl_id.code),
            sector=verificateur.sector,
            matricule=verificateur.matricule,
        )
