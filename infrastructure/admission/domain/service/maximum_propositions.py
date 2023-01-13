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
from django.db.models import Value, IntegerField, Count, Q

from admission.contrib.models import GeneralEducationAdmission, ContinuingEducationAdmission, DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionDoctorale,
    STATUTS_PROPOSITION_AVANT_SOUMISSION,
)
from admission.ddd.admission.domain.service.i_maximum_propositions import IMaximumPropositionsAutorisees
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutProposition as ChoixStatutPropositionContinue,
)
from base.models.person import Person


class MaximumPropositionsAutorisees(IMaximumPropositionsAutorisees):
    @classmethod
    def nb_propositions_envoyees_formation_generale(cls, matricule: str) -> int:
        return GeneralEducationAdmission.objects.filter(
            candidate__global_id=matricule,
            status=ChoixStatutPropositionGenerale.SUBMITTED.name,
        ).count()

    @classmethod
    def nb_propositions_envoyees_formation_continue(cls, matricule: str) -> int:
        return ContinuingEducationAdmission.objects.filter(
            candidate__global_id=matricule,
            status=ChoixStatutPropositionContinue.SUBMITTED.name,
        ).count()

    @classmethod
    def nb_propositions_envoyees_formation_doctorale(cls, matricule: str) -> int:
        return DoctorateAdmission.objects.filter(
            candidate__global_id=matricule,
            status=ChoixStatutPropositionDoctorale.SUBMITTED.name,
        ).count()

    @classmethod
    def nb_propositions_en_cours(cls, matricule: str) -> int:
        nb_propositions = (
            Person.objects.annotate(
                doctorate_propositions_nb=Count(
                    'baseadmissions__doctorateadmission',
                    filter=Q(
                        baseadmissions__doctorateadmission__status__in=STATUTS_PROPOSITION_AVANT_SOUMISSION,
                    ),
                ),
                general_propositions_nb=Count(
                    'baseadmissions__generaleducationadmission',
                    filter=Q(
                        baseadmissions__generaleducationadmission__status=(
                            ChoixStatutPropositionGenerale.IN_PROGRESS.name
                        ),
                    ),
                ),
                continuing_propositions_nb=Count(
                    'baseadmissions__continuingeducationadmission',
                    filter=Q(
                        baseadmissions__continuingeducationadmission__status=(
                            ChoixStatutPropositionContinue.IN_PROGRESS.name
                        ),
                    ),
                ),
            )
            .values_list(
                'doctorate_propositions_nb',
                'general_propositions_nb',
                'continuing_propositions_nb',
            )
            .get(global_id=matricule)
        )
        return sum(nb_propositions)
