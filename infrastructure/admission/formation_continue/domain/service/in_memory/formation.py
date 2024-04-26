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
from typing import List, Optional

import factory

from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.domain.model.formation import Formation, FormationIdentity
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.domain.service.i_formation import IFormationContinueTranslator
from admission.ddd.admission.formation_continue.domain.validator.exceptions import FormationNonTrouveeException
from admission.ddd.admission.test.factory.formation import FormationFactory
from base.models.enums.education_group_types import TrainingType
from base.models.enums.state_iufc import StateIUFC
from ddd.logic.formation_catalogue.formation_continue.domain.model.informations_specifiques import (
    InformationsSpecifiques,
    FormationContinueIdentite,
)
from ddd.logic.formation_catalogue.formation_continue.domain.validator.exceptions import (
    InformationsSpecifiquesNonTrouveesException,
)
from ddd.logic.formation_catalogue.formation_continue.dtos.informations_specifiques import InformationsSpecifiquesDTO
from infrastructure.formation_catalogue.formation_continue.repository.in_memory.informations_specifiques import (
    InformationsSpecifiquesInMemoryRepository,
)


class InformationsSpecifiquesFactory(factory.Factory):
    class Meta:
        model = InformationsSpecifiques

    aide_a_la_formation = True
    inscription_au_role_obligatoire = False
    etat = StateIUFC.OPEN


class FormationContinueInformationsSpecifiquesInMemoryRepositoryFactory(InformationsSpecifiquesInMemoryRepository):
    _informations_specifiques = [
        InformationsSpecifiquesFactory(
            entity_id=FormationContinueIdentite(
                sigle_formation='USCC1',
                annee=2022,
            ),
        ),
        InformationsSpecifiquesFactory(
            entity_id=FormationContinueIdentite(
                sigle_formation='USCC1',
                annee=2020,
            ),
        ),
        InformationsSpecifiquesFactory(
            entity_id=FormationContinueIdentite(
                sigle_formation='USCC2',
                annee=2022,
            ),
        ),
        InformationsSpecifiquesFactory(
            entity_id=FormationContinueIdentite(
                sigle_formation='USCC3',
                annee=2022,
            ),
        ),
        InformationsSpecifiquesFactory(
            entity_id=FormationContinueIdentite(
                sigle_formation='USCC4',
                annee=2022,
            ),
            inscription_au_role_obligatoire=True,
        ),
        InformationsSpecifiquesFactory(
            entity_id=FormationContinueIdentite(
                sigle_formation='USCC5',
                annee=2022,
            ),
        ),
        InformationsSpecifiquesFactory(
            entity_id=FormationContinueIdentite(
                sigle_formation='ESP3DP-MASTER',
                annee=2022,
            ),
        ),
        InformationsSpecifiquesFactory(
            entity_id=FormationContinueIdentite(
                sigle_formation='USCC4',
                annee=2020,
            ),
            inscription_au_role_obligatoire=True,
        ),
    ]


class FormationContinueInMemoryTranslator(IFormationContinueTranslator):
    trainings = [
        FormationFactory(
            intitule='Formation USCC1',
            entity_id__sigle='USCC1',
            entity_id__annee=2022,
            type=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,
            campus__nom='Mons',
            campus_inscription__nom='Mons',
            sigle_entite_gestion='FC1',
        ),
        FormationFactory(
            intitule='Formation USCC1',
            entity_id__sigle='USCC1',
            entity_id__annee=2020,
            type=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,
            campus__nom='Louvain-la-Neuve',
            campus_inscription__nom='Louvain-la-Neuve',
            sigle_entite_gestion='FC1',
        ),
        FormationFactory(
            intitule='Formation USCC2',
            entity_id__sigle='USCC2',
            entity_id__annee=2022,
            type=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,
            campus__nom='Louvain-la-Neuve',
            campus_inscription__nom='Louvain-la-Neuve',
            sigle_entite_gestion='FC1',
        ),
        FormationFactory(
            intitule='Formation USCC3',
            entity_id__sigle='USCC3',
            entity_id__annee=2022,
            type=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,
            campus__nom='Charleroi',
            campus_inscription__nom='Charleroi',
            sigle_entite_gestion='FC1',
        ),
        FormationFactory(
            intitule='Formation USCC3',
            entity_id__sigle='USCC3',
            entity_id__annee=2020,
            type=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,
            campus__nom='Charleroi',
            campus_inscription__nom='Charleroi',
            sigle_entite_gestion='FC1',
        ),
        FormationFactory(
            intitule='Formation USCC4',
            entity_id__sigle='USCC4',
            entity_id__annee=2022,
            type=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,
            campus__nom='Louvain-la-Neuve',
            campus_inscription__nom='Louvain-la-Neuve',
            sigle_entite_gestion='FC1',
        ),
        FormationFactory(
            intitule='Formation USCC5',
            entity_id__sigle='USCC5',
            entity_id__annee=2022,
            type=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,
            campus__nom='Charleroi',
            campus_inscription__nom='Charleroi',
            sigle_entite_gestion='FC1',
        ),
        FormationFactory(
            intitule='Master ESP3DP',
            entity_id__sigle='ESP3DP-MASTER',
            entity_id__annee=2022,
            type=TrainingType.MASTER_M1,
            campus__nom='Charleroi',
            campus_inscription__nom='Charleroi',
            sigle_entite_gestion='FC2',
        ),
        FormationFactory(
            intitule='Formation USCC4',
            entity_id__sigle='USCC4',
            entity_id__annee=2020,
            type=TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,
            campus__nom='Louvain-la-Neuve',
            campus_inscription__nom='Louvain-la-Neuve',
            sigle_entite_gestion='FC1',
        ),
    ]

    iufc_specific_informations_trainings_repository = FormationContinueInformationsSpecifiquesInMemoryRepositoryFactory

    @classmethod
    def _build_dto(cls, entity: FormationFactory) -> 'FormationDTO':
        return FormationDTO(
            sigle=entity.entity_id.sigle,
            annee=entity.entity_id.annee,
            date_debut=None,
            intitule=entity.intitule,
            intitule_fr=entity.intitule,
            intitule_en=entity.intitule,
            campus=entity.campus,
            type=entity.type.name,
            code_domaine=entity.code_domaine,
            sigle_entite_gestion=entity.sigle_entite_gestion,
            campus_inscription=entity.campus_inscription,
            code=entity.code,
            credits=entity.credits,
        )

    @classmethod
    def get_dto(cls, sigle: str, annee: int) -> 'FormationDTO':
        formation_entity_id = FormationIdentity(sigle=sigle, annee=annee)
        training = next(
            (
                training
                for training in cls.trainings
                if training.entity_id == formation_entity_id
                and training.type_formation == TypeFormation.FORMATION_CONTINUE
            ),
            None,
        )
        return cls._build_dto(entity=training)

    @classmethod
    def get(cls, entity_id: FormationIdentity) -> 'Formation':
        training = next(
            (
                training
                for training in cls.trainings
                if training.entity_id == entity_id and training.type_formation == TypeFormation.FORMATION_CONTINUE
            ),
            None,
        )

        if training:
            return Formation(
                entity_id=training.entity_id,
                type=training.type,
                code_domaine=training.code_domaine,
                campus=training.campus or '',
            )

        raise FormationNonTrouveeException

    @classmethod
    def search(cls, annee: Optional[int], terme_de_recherche: str, campus: Optional[str]) -> List['FormationDTO']:
        return [
            cls._build_dto(entity=training)
            for training in cls.trainings
            if training.entity_id.annee == annee
            and (terme_de_recherche in training.intitule or terme_de_recherche in training.entity_id.sigle)
            and (not campus or training.campus.nom == campus)
        ]

    @classmethod
    def verifier_existence(cls, sigle: str, annee: int) -> bool:  # pragma: no cover
        return any(
            True
            for training in cls.trainings
            if training.entity_id.sigle == sigle
            and training.entity_id.annee == annee
            and training.type_formation == TypeFormation.FORMATION_CONTINUE
        )

    @classmethod
    def get_informations_specifiques_dto(cls, entity_id: FormationIdentity) -> Optional[InformationsSpecifiquesDTO]:
        try:
            return cls.iufc_specific_informations_trainings_repository.get_dto(
                entity_id=FormationContinueIdentite(
                    sigle_formation=entity_id.sigle,
                    annee=entity_id.annee,
                )
            )
        except InformationsSpecifiquesNonTrouveesException:
            pass
