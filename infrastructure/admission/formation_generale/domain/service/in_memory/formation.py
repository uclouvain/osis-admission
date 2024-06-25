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

from admission.ddd import CODE_BACHELIER_VETERINAIRE
from admission.ddd.admission.domain.enums import TYPES_FORMATION_GENERALE
from admission.ddd.admission.domain.model.formation import Formation, FormationIdentity
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_generale.domain.service.i_formation import IFormationGeneraleTranslator
from admission.ddd.admission.formation_generale.domain.validator.exceptions import FormationNonTrouveeException
from admission.ddd.admission.test.factory.formation import FormationFactory
from base.models.enums.education_group_types import TrainingType


class FormationGeneraleInMemoryTranslator(IFormationGeneraleTranslator):
    trainings = [
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2022,
            type=TrainingType.BACHELOR,
            campus__nom='Mons',
        ),
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2021,
            type=TrainingType.BACHELOR,
            campus__nom='Mons',
        ),
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2020,
            type=TrainingType.BACHELOR,
            campus__nom='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2020,
            type=TrainingType.BACHELOR,
            campus__nom='Mons',
        ),
        FormationFactory(
            intitule='Bachelier vétérinaire',
            entity_id__sigle=CODE_BACHELIER_VETERINAIRE,
            entity_id__annee=2020,
            type=TrainingType.BACHELOR,
            campus__nom='Mons',
            code_domaine='11A',
        ),
        FormationFactory(
            intitule='Master en sciences',
            entity_id__sigle='MASTER-SCI',
            entity_id__annee=2022,
            type=TrainingType.MASTER_M1,
            campus__nom='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2022,
            type=TrainingType.BACHELOR,
            campus__nom='Charleroi',
        ),
        FormationFactory(
            intitule='Formation SC3DP',
            entity_id__sigle='SC3DP',
            entity_id__annee=2022,
            type=TrainingType.CERTIFICATE,
            campus__nom='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Formation ESP3DP',
            entity_id__sigle='ESP3DP',
            entity_id__annee=2022,
            type=TrainingType.MASTER_M1,
            campus__nom='Charleroi',
        ),
        FormationFactory(
            intitule='Formation continue ESP3DP',
            entity_id__sigle='ES3DP-CONTINUE',
            entity_id__annee=2022,
            type=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE,
            campus__nom='Charleroi',
        ),
        FormationFactory(
            intitule='Master en sciences',
            entity_id__sigle='MASTER-SCI',
            entity_id__annee=2021,
            type=TrainingType.MASTER_M1,
            campus__nom='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Master en sciences',
            entity_id__sigle='MASTER-SCI-UNKNOWN-CAMPUS',
            entity_id__annee=2021,
            type=TrainingType.MASTER_M1,
            campus__nom='Unknown campus',
        ),
        FormationFactory(
            intitule='Master en sciences',
            entity_id__sigle='MASTER-SCI',
            entity_id__annee=2020,
            type=TrainingType.MASTER_M1,
            campus__nom='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Aggrégation en économie',
            entity_id__sigle='AGGREGATION-ECO',
            entity_id__annee=2020,
            type=TrainingType.AGGREGATION,
            campus__nom='Charleroi',
        ),
        FormationFactory(
            intitule='CAPAES en économie',
            entity_id__sigle='CAPAES-ECO',
            entity_id__annee=2020,
            type=TrainingType.CAPAES,
            campus__nom='Charleroi',
        ),
        FormationFactory(
            intitule='Bachelier vétérinaire',
            entity_id__sigle=CODE_BACHELIER_VETERINAIRE,
            entity_id__annee=2021,
            type=TrainingType.BACHELOR,
            campus__nom='Mons',
            code_domaine='11A',
        ),
        FormationFactory(
            intitule='Aggrégation en économie',
            entity_id__sigle='AGGREGATION-ECO',
            entity_id__annee=2021,
            type=TrainingType.AGGREGATION,
            campus__nom='Charleroi',
        ),
        FormationFactory(
            intitule='CAPAES en économie',
            entity_id__sigle='CAPAES-ECO',
            entity_id__annee=2021,
            type=TrainingType.CAPAES,
            campus__nom='Charleroi',
        ),
        FormationFactory(
            intitule='Certificate in business',
            entity_id__sigle='CERTIF-BUS',
            entity_id__annee=2021,
            type=TrainingType.CERTIFICATE,
            campus__nom='Charleroi',
        ),
        FormationFactory(
            intitule='Master en sciences',
            entity_id__sigle='ABCD2MC',
            entity_id__annee=2024,
            type=TrainingType.MASTER_M1,
            campus__nom='Louvain-la-Neuve',
        ),
    ]

    @classmethod
    def _build_dto(cls, entity: FormationFactory) -> 'FormationDTO':
        return FormationDTO(
            sigle=entity.entity_id.sigle,
            code=entity.code,
            annee=entity.entity_id.annee,
            date_debut=None,
            intitule=entity.intitule,
            intitule_fr=entity.intitule,
            intitule_en=entity.intitule,
            campus=entity.campus,
            type=entity.type.name,
            code_domaine=entity.code_domaine,
            campus_inscription=entity.campus_inscription,
            sigle_entite_gestion=entity.sigle_entite_gestion,
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
                and training.type_formation.name in TYPES_FORMATION_GENERALE
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
                if training.entity_id == entity_id and training.type_formation.name in TYPES_FORMATION_GENERALE
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
    def search(
        cls,
        type: str,
        annee: Optional[int],
        sigle: Optional[str],
        intitule: Optional[str],
        terme_de_recherche: Optional[str],
        campus: Optional[str],
    ) -> List['FormationDTO']:
        return [
            cls._build_dto(entity=training)
            for training in cls.trainings
            if training.entity_id.annee == annee
            and training.type_formation.name == type
            and (
                (intitule and intitule in training.intitule)
                or (terme_de_recherche and terme_de_recherche in training.intitule)
            )
            and (not campus or training.campus.nom == campus)
        ]

    @classmethod
    def verifier_existence(cls, sigle: str, annee: int) -> bool:
        return any(
            training
            for training in cls.trainings
            if training.entity_id.sigle == sigle
            and training.entity_id.annee == annee
            and training.type_formation.name in TYPES_FORMATION_GENERALE
        )
