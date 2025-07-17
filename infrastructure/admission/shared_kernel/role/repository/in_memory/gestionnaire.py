##############################################################################
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
##############################################################################
from typing import List

from admission.ddd import CODE_BACHELIER_VETERINAIRE
from admission.ddd.admission.shared_kernel.dtos.formation import BaseFormationDTO
from admission.ddd.admission.shared_kernel.role.repository.gestionnaire import IGestionnaireRepository
from admission.ddd.admission.shared_kernel.tests.factory.formation import FormationFactory
from base.models.enums.education_group_types import TrainingType


class GestionnaireInMemoryRepository(IGestionnaireRepository):
    trainings = [
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2022,
            type=TrainingType.BACHELOR,
            campus='Mons',
        ),
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2021,
            type=TrainingType.BACHELOR,
            campus='Mons',
        ),
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2020,
            type=TrainingType.BACHELOR,
            campus='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2020,
            type=TrainingType.BACHELOR,
            campus='Mons',
        ),
        FormationFactory(
            intitule='Bachelier vétérinaire',
            entity_id__sigle=CODE_BACHELIER_VETERINAIRE,
            entity_id__annee=2020,
            type=TrainingType.BACHELOR,
            campus='Mons',
            code_domaine='11A',
        ),
        FormationFactory(
            intitule='Master en sciences',
            entity_id__sigle='MASTER-SCI',
            entity_id__annee=2022,
            type=TrainingType.MASTER_M1,
            campus='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Master MC',
            entity_id__sigle='MASTER-MC',
            entity_id__annee=2022,
            type=TrainingType.MASTER_MC,
            campus='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Master M4',
            entity_id__sigle='MASTER-M4',
            entity_id__annee=2022,
            type=TrainingType.MASTER_M4,
            campus='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Master M5',
            entity_id__sigle='MASTER-M5',
            entity_id__annee=2022,
            type=TrainingType.MASTER_M5,
            campus='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Bachelier en sciences économiques et de gestion',
            entity_id__sigle='BACHELIER-ECO',
            entity_id__annee=2022,
            type=TrainingType.BACHELOR,
            campus='Charleroi',
        ),
        FormationFactory(
            intitule='Formation SC3DP',
            entity_id__sigle='SC3DP',
            entity_id__annee=2022,
            type=TrainingType.CERTIFICATE,
            campus='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Formation ESP3DP',
            entity_id__sigle='ESP3DP',
            entity_id__annee=2022,
            type=TrainingType.MASTER_M1,
            campus='Charleroi',
        ),
        FormationFactory(
            intitule='Formation continue ESP3DP',
            entity_id__sigle='ES3DP-CONTINUE',
            entity_id__annee=2022,
            type=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE,
            campus='Charleroi',
        ),
        FormationFactory(
            intitule='Master en sciences',
            entity_id__sigle='MASTER-SCI',
            entity_id__annee=2021,
            type=TrainingType.MASTER_M1,
            campus='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Master en sciences',
            entity_id__sigle='MASTER-SCI',
            entity_id__annee=2020,
            type=TrainingType.MASTER_M1,
            campus='Louvain-la-Neuve',
        ),
        FormationFactory(
            intitule='Aggrégation en économie',
            entity_id__sigle='AGGREGATION-ECO',
            entity_id__annee=2020,
            type=TrainingType.AGGREGATION,
            campus='Charleroi',
        ),
        FormationFactory(
            intitule='CAPAES en économie',
            entity_id__sigle='CAPAES-ECO',
            entity_id__annee=2020,
            type=TrainingType.CAPAES,
            campus='Charleroi',
        ),
        FormationFactory(
            intitule='Bachelier vétérinaire',
            entity_id__sigle=CODE_BACHELIER_VETERINAIRE,
            entity_id__annee=2021,
            type=TrainingType.BACHELOR,
            campus='Mons',
            code_domaine='11A',
        ),
        FormationFactory(
            intitule='Aggrégation en économie',
            entity_id__sigle='AGGREGATION-ECO',
            entity_id__annee=2021,
            type=TrainingType.AGGREGATION,
            campus='Charleroi',
        ),
        FormationFactory(
            intitule='CAPAES en économie',
            entity_id__sigle='CAPAES-ECO',
            entity_id__annee=2021,
            type=TrainingType.CAPAES,
            campus='Charleroi',
        ),
        FormationFactory(
            intitule='Certificate of participation in business',
            entity_id__sigle='CERTIF-BUS',
            entity_id__annee=2021,
            type=TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
            campus='Charleroi',
        ),
    ]

    @classmethod
    def rechercher_formations_gerees(
        cls,
        matriculaire_gestionnaire: str,
        annee: int,
        terme_recherche: str,
    ) -> List['BaseFormationDTO']:
        return [
            BaseFormationDTO(
                sigle=training.entity_id.sigle,
                intitule=training.intitule,
                lieu_enseignement=training.campus,
                uuid='',
                annee=training.entity_id.annee,
            )
            for training in cls.trainings
            if terme_recherche in f'{training.intitule} {training.entity_id.sigle}'
            and training.entity_id.annee == annee
        ]
