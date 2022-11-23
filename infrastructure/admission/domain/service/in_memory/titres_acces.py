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
from typing import List

from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.dtos.conditions import AdmissionConditionsDTO
from admission.tests.factories.conditions import AdmissionConditionsDTOFactory


class TitresAccesInMemory(ITitresAcces):
    results = {
        '0123456789': AdmissionConditionsDTOFactory(
            diplomation_potentiel_doctorat_belge=True,
        ),
        '0000000001': AdmissionConditionsDTOFactory(
            diplomation_academique_belge=True,
            potentiel_acces_vae=True,
        ),
    }

    @classmethod
    def conditions_remplies(cls, matricule_candidat: str, equivalence_diplome: List[str]) -> AdmissionConditionsDTO:
        return cls.results.get(matricule_candidat, AdmissionConditionsDTOFactory())
