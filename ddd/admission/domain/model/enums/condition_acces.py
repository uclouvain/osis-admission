# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import Dict, List

from django.utils.translation import gettext_lazy as _

from base.models.enums.education_group_types import TrainingType
from base.models.utils.utils import ChoiceEnum
from epc.models.enums.condition_acces import ConditionAcces


def recuperer_conditions_acces_par_formation(type_formation: str):
    """Récupérer une liste des choix des conditions d'accès pour une formation donnée."""
    return [(choice.name, choice.label) for choice in CHOIX_PAR_FORMATION.get(type_formation, [])]


CHOIX_POUR_BACHELIER = [
    ConditionAcces.SECONDAIRE,
    ConditionAcces.EXAMEN_ADMISSION,
    ConditionAcces.PARCOURS,
    ConditionAcces.VAE,
    ConditionAcces.MASTER,
    ConditionAcces.BAC,
    ConditionAcces.UNI_SNU_AUTRE,
]

CHOIX_POUR_MASTER = [
    ConditionAcces.BAC,
    ConditionAcces.BAMA15,
    ConditionAcces.SNU_TYPE_LONG_1ER_CYCLE,
    ConditionAcces.SNU_TYPE_LONG_2EME_CYCLE,
    ConditionAcces.VALORISATION_180_ECTS,
    ConditionAcces.VAE,
    ConditionAcces.PARCOURS,
    ConditionAcces.MASTER,
    ConditionAcces.UNI_SNU_AUTRE,
]

CHOIX_POUR_MASTER_DE_SPECIALISATION = [
    ConditionAcces.MASTER,
    ConditionAcces.VALORISATION_240_ECTS,
    ConditionAcces.VAE,
    ConditionAcces.PARCOURS,
    ConditionAcces.UNI_SNU_AUTRE,
]

CHOIX_POUR_AGGREGATION = [
    ConditionAcces.MASTER,
    ConditionAcces.PARCOURS,
    ConditionAcces.MASTER_EPM,
    ConditionAcces.UNI_SNU_AUTRE,
]

CHOIX_POUR_CAPAES = [
    ConditionAcces.MASTER,
    ConditionAcces.PARCOURS,
    ConditionAcces.UNI_SNU_AUTRE,
    ConditionAcces.VALORISATION_180_ECTS,
    ConditionAcces.VAE,
]

CHOIX_POUR_DOCTORAT = [
    ConditionAcces.MASTER,
    ConditionAcces.UNI_SNU_AUTRE,
    ConditionAcces.VALORISATION_300_ECTS,
    ConditionAcces.PARCOURS,
]

CHOIX_POUR_CERTIFICAT = [
    ConditionAcces.BAC,
    ConditionAcces.MASTER,
    ConditionAcces.VALORISATION_180_ECTS,
    ConditionAcces.VAE,
    ConditionAcces.PARCOURS,
    ConditionAcces.UNI_SNU_AUTRE,
]

CHOIX_PAR_FORMATION: Dict[str, List[ConditionAcces]] = {
    TrainingType.BACHELOR.name: CHOIX_POUR_BACHELIER,
    TrainingType.MASTER_MC.name: CHOIX_POUR_MASTER_DE_SPECIALISATION,
    TrainingType.MASTER_MA_120.name: CHOIX_POUR_MASTER,
    TrainingType.MASTER_MD_120.name: CHOIX_POUR_MASTER,
    TrainingType.MASTER_MS_120.name: CHOIX_POUR_MASTER,
    TrainingType.MASTER_MS_180_240.name: CHOIX_POUR_MASTER,
    TrainingType.MASTER_M1.name: CHOIX_POUR_MASTER,
    TrainingType.RESEARCH_CERTIFICATE.name: {},
    TrainingType.CERTIFICATE.name: CHOIX_POUR_CERTIFICAT,
    TrainingType.AGGREGATION.name: CHOIX_POUR_AGGREGATION,
    TrainingType.CAPAES.name: CHOIX_POUR_CAPAES,
    TrainingType.PHD.name: CHOIX_POUR_DOCTORAT,
}


class TypeTitreAccesSelectionnable(ChoiceEnum):
    EXPERIENCE_ACADEMIQUE = _('Academic experience')
    EXPERIENCE_NON_ACADEMIQUE = _('Non-academic experience')
    ETUDES_SECONDAIRES = _('Secondary studies')
