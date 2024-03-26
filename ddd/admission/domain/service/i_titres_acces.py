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
from enum import Enum
from typing import List, Mapping, Optional, Tuple

from admission.ddd.admission.domain.validator.exceptions import ConditionsAccessNonRempliesException
from admission.ddd.admission.dtos.conditions import AdmissionConditionsDTO
from base.models.enums.education_group_types import TrainingType
from osis_common.ddd import interface


class ConditionAccess(str, Enum):
    DIPLOMATION_POTENTIEL_MASTER_BELGE = 'diplomation_potentiel_master_belge'
    POTENTIEL_MASTER_BELGE_SANS_DIPLOMATION = 'potentiel_master_belge_sans_diplomation'
    DIPLOMATION_POTENTIEL_MASTER_ETRANGER = 'diplomation_potentiel_master_etranger'
    DIPLOMATION_SECONDAIRE_BELGE = 'diplomation_secondaire_belge'
    DIPLOMATION_SECONDAIRE_ETRANGER = 'diplomation_secondaire_etranger'
    ALTERNATIVE_ETUDES_SECONDAIRES = 'alternative_etudes_secondaires'
    DIPLOMATION_ACADEMIQUE_BELGE = 'diplomation_academique_belge'
    POTENTIEL_ACCES_VAE = 'potentiel_acces_vae'
    DIPLOMATION_ACADEMIQUE_ETRANGER = 'diplomation_academique_etranger'
    POTENTIEL_BACHELIER_BELGE_SANS_DIPLOMATION = 'potentiel_bachelier_belge_sans_diplomation'
    DIPLOMATION_POTENTIEL_DOCTORAT_BELGE = 'diplomation_potentiel_doctorat_belge'


class Titres:
    def __init__(self, obj: AdmissionConditionsDTO, *conditions: ConditionAccess):
        self.condition_obj = obj
        self.condition_names = conditions

    def __bool__(self):
        return not self.condition_names or any(self.get_valid_conditions())

    def __str__(self):  # pragma: no cover
        return ','.join([cond.name for cond in self.get_valid_conditions()])

    def get_valid_conditions(self):
        return [cond for cond in self.condition_names if getattr(self.condition_obj, cond.value, False)]


class ITitresAcces(interface.DomainService):
    condition_matrix: Mapping[Tuple[TrainingType, ...], List[ConditionAccess]] = {
        (TrainingType.AGGREGATION,): [
            ConditionAccess.DIPLOMATION_POTENTIEL_MASTER_BELGE,
            ConditionAccess.POTENTIEL_MASTER_BELGE_SANS_DIPLOMATION,
            ConditionAccess.DIPLOMATION_POTENTIEL_MASTER_ETRANGER,
        ],
        (TrainingType.CAPAES,): [
            ConditionAccess.DIPLOMATION_POTENTIEL_MASTER_BELGE,
            ConditionAccess.DIPLOMATION_POTENTIEL_MASTER_ETRANGER,
        ],
        (TrainingType.BACHELOR,): [
            ConditionAccess.DIPLOMATION_SECONDAIRE_BELGE,
            ConditionAccess.DIPLOMATION_SECONDAIRE_ETRANGER,
            ConditionAccess.ALTERNATIVE_ETUDES_SECONDAIRES,
            ConditionAccess.DIPLOMATION_ACADEMIQUE_BELGE,
            ConditionAccess.POTENTIEL_ACCES_VAE,
        ],
        (
            TrainingType.MASTER_MA_120,
            TrainingType.MASTER_MD_120,
            TrainingType.MASTER_MS_120,
            TrainingType.MASTER_MA_180_240,
            TrainingType.MASTER_MD_180_240,
            TrainingType.MASTER_MS_180_240,
            TrainingType.MASTER_M1,
        ): [
            ConditionAccess.DIPLOMATION_ACADEMIQUE_BELGE,
            ConditionAccess.DIPLOMATION_ACADEMIQUE_ETRANGER,
            ConditionAccess.POTENTIEL_BACHELIER_BELGE_SANS_DIPLOMATION,
            ConditionAccess.POTENTIEL_ACCES_VAE,
        ],
        (TrainingType.MASTER_MC,): [
            ConditionAccess.DIPLOMATION_POTENTIEL_MASTER_BELGE,
            ConditionAccess.DIPLOMATION_POTENTIEL_DOCTORAT_BELGE,
            ConditionAccess.DIPLOMATION_ACADEMIQUE_ETRANGER,
            ConditionAccess.POTENTIEL_ACCES_VAE,
        ],
        (TrainingType.PHD,): [
            ConditionAccess.DIPLOMATION_POTENTIEL_MASTER_BELGE,
            ConditionAccess.DIPLOMATION_POTENTIEL_DOCTORAT_BELGE,
            ConditionAccess.DIPLOMATION_ACADEMIQUE_ETRANGER,
        ],
        (TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE,): [
            ConditionAccess.DIPLOMATION_ACADEMIQUE_BELGE,
            ConditionAccess.DIPLOMATION_ACADEMIQUE_ETRANGER,
            ConditionAccess.POTENTIEL_ACCES_VAE,
        ],
        (TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,): [
            ConditionAccess.DIPLOMATION_ACADEMIQUE_BELGE,
            ConditionAccess.DIPLOMATION_ACADEMIQUE_ETRANGER,
            ConditionAccess.POTENTIEL_ACCES_VAE,
        ],
        (
            TrainingType.CERTIFICATE_OF_PARTICIPATION,
            TrainingType.CERTIFICATE_OF_SUCCESS,
        ): [],
        (
            TrainingType.CERTIFICATE,
            TrainingType.RESEARCH_CERTIFICATE,
        ): [],
    }

    formations_sans_conditions_acces = {
        type_formation
        for types_formation, titres in condition_matrix.items()
        if titres == []
        for type_formation in types_formation
    }

    @classmethod
    def conditions_remplies(cls, matricule_candidat: str, equivalence_diplome: List[str]) -> AdmissionConditionsDTO:
        raise NotImplementedError

    @classmethod
    def recuperer_titres_access(
        cls,
        matricule_candidat: str,
        type_formation: 'TrainingType',
        equivalence_diplome: Optional[List[str]] = None,
    ) -> Titres:
        conditions = cls.conditions_remplies(matricule_candidat, equivalence_diplome or [])
        titres_requis: List[ConditionAccess] = next(
            (titres for types, titres in cls.condition_matrix.items() if type_formation in types), []
        )
        return Titres(conditions, *titres_requis)

    @classmethod
    def verifier(
        cls,
        matricule_candidat: str,
        type_formation: 'TrainingType',
        equivalence_diplome: Optional[List[str]] = None,
    ):
        if not cls.recuperer_titres_access(matricule_candidat, type_formation, equivalence_diplome):
            raise ConditionsAccessNonRempliesException

    @classmethod
    def verifier_titres(cls, titres: 'Titres'):
        if not titres:
            raise ConditionsAccessNonRempliesException
