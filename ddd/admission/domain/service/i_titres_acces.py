# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Mapping, Tuple

from admission.ddd.admission.domain.validator.exceptions import ConditionsAccessNonRempliesException
from admission.ddd.admission.dtos.conditions import AdmissionConditionsDTO
from base.models.enums.education_group_types import TrainingType
from osis_common.ddd import interface


class Conditions:
    def __init__(self, obj: AdmissionConditionsDTO, *conditions: str):
        self.condition_obj = obj
        self.condition_names = conditions

    def __bool__(self):
        return any(self.get_valid_conditions())

    def __str__(self):  # pragma: no cover
        return ','.join([name for name in self.condition_names if getattr(self.condition_obj, name, False)])

    def get_valid_conditions(self):
        return [getattr(self.condition_obj, name, False) for name in self.condition_names]


class ITitresAcces(interface.DomainService):
    @classmethod
    def conditions_remplies(cls, matricule_candidat: str) -> AdmissionConditionsDTO:
        raise NotImplementedError

    @classmethod
    def verifier(cls, matricule_candidat: str, type_formation: TrainingType):
        # Condition matrix
        conditions = cls.conditions_remplies(matricule_candidat)
        condition_matrix: Mapping[Tuple[TrainingType, ...], List[str]] = {
            (TrainingType.AGGREGATION,): [
                'diplomation_potentiel_master_belge',
                'potentiel_master_belge_sans_diplomation',
                'diplomation_potentiel_master_etranger',
            ],
            (TrainingType.CAPAES,): [
                'diplomation_potentiel_master_belge',
                'diplomation_potentiel_master_etranger',
            ],
            (TrainingType.BACHELOR,): [
                'diplomation_secondaire_belge',
                'diplomation_secondaire_etranger',
                'alternative_etudes_secondaires',
                'diplomation_academique_belge',
                'potentiel_acces_vae',
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
                'diplomation_academique_belge',
                'diplomation_academique_etranger',
                'potentiel_bachelier_belge_sans_diplomation',
                'potentiel_acces_vae',
            ],
            (TrainingType.MASTER_MC,): [
                'diplomation_potentiel_master_belge',
                'diplomation_potentiel_doctorat_belge',
                'diplomation_academique_etranger',
                'potentiel_acces_vae',
            ],
            (TrainingType.PHD,): [
                'diplomation_potentiel_master_belge',
                'diplomation_potentiel_doctorat_belge',
                'diplomation_academique_etranger',
            ],
            (TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE,): [
                'diplomation_academique_belge',
                'diplomation_academique_etranger',
                'potentiel_acces_vae',
            ],
            (TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE,): [
                'diplomation_academique_belge',
                'diplomation_academique_etranger',
                'potentiel_acces_vae',
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
        titres_requis: List[str] = next(
            (titres for types, titres in condition_matrix.items() if type_formation in types), []
        )
        if titres_requis and not Conditions(conditions, *titres_requis):
            raise ConditionsAccessNonRempliesException

    @classmethod
    def verifier_doctorat(cls, matricule_candidat: str):
        cls.verifier(matricule_candidat, TrainingType.PHD)
