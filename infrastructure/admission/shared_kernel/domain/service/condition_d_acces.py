# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.shared_kernel.domain.model.enums.condition_acces import ErreurConditionAcces
from admission.ddd.admission.shared_kernel.domain.service.conditions_d_acces import IConditionDAcces
from admission.models import GeneralEducationAdmission, DoctorateAdmission
from ddd.logic.condition_acces.domain.service.calcul_condition_acces import ConditionAccesInsuffisant, \
    ConditionAccesIncomplet


class ConditionDAcces(IConditionDAcces):

    @classmethod
    def calculer_condition_d_acces(cls, uuid_proposition: str):
        # TODO Appeler le translator qui invoke calculer_condition_acces puis sauvegarder les infos sur l'admission
        try:
            condition_acces = TRANSLATOR.calculer(uuid_proposition)
            if condition_acces is None:
                admission_requirement = ''
                admission_requirement_year = None
                admission_requirement_error = ''
            else:
                admission_requirement = condition_acces.condition
                admission_requirement_year = condition_acces.millesime
                admission_requirement_error = ''
        except ConditionAccesInsuffisant:
            admission_requirement = ''
            admission_requirement_year = None
            admission_requirement_error = ErreurConditionAcces.INSUFFISANT.name
        except ConditionAccesIncomplet:
            admission_requirement = ''
            admission_requirement_year = None
            admission_requirement_error = ErreurConditionAcces.INCOMPLET.name

        GeneralEducationAdmission.objects.filter(uuid=uuid_proposition).update(
            admission_requirement=admission_requirement,
            admission_requirement_year=admission_requirement_year,
            admission_requirement_error=admission_requirement_error,
        )
        DoctorateAdmission.objects.filter(uuid=uuid_proposition).update(
            admission_requirement=admission_requirement,
            admission_requirement_year=admission_requirement_year,
            admission_requirement_error=admission_requirement_error,
        )

        return condition_acces
