# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Union

from django.db.models import F

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition as PropositionDoctorale,
)
from admission.ddd.admission.domain.service.i_raccrocher_experiences_curriculum import (
    IRaccrocherExperiencesCurriculum,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import (
    Proposition as PropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition as PropositionGenerale,
)
from admission.models.base import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
    BaseAdmission,
)
from osis_profile.models import EducationalExperience, ProfessionalExperience


class RaccrocherExperiencesCurriculum(IRaccrocherExperiencesCurriculum):
    @classmethod
    def raccrocher(
        cls,
        proposition: Union[PropositionContinue, PropositionDoctorale, PropositionGenerale],
    ):
        if proposition.statut not in {
            ChoixStatutPropositionDoctorale.CONFIRMEE,
            ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE,
            ChoixStatutPropositionContinue.CONFIRMEE,
            ChoixStatutPropositionGenerale.CONFIRMEE,
        }:
            return

        if isinstance(
            proposition,
            (PropositionContinue, PropositionGenerale),
        ):
            BaseAdmission.objects.filter(uuid=proposition.entity_id.uuid).update(
                valuated_secondary_studies_person_id=F('candidate_id'),
            )

        educational_experiences_uuids = EducationalExperience.objects.filter(
            person__global_id=proposition.matricule_candidat,
        ).values_list('uuid', flat=True)

        professional_experiences_uuids = ProfessionalExperience.objects.filter(
            person__global_id=proposition.matricule_candidat,
        ).values_list('uuid', flat=True)

        educational_experiences_valuations = [
            AdmissionEducationalValuatedExperiences(
                baseadmission_id=proposition.entity_id.uuid,
                educationalexperience_id=experience_uuid,
            )
            for experience_uuid in educational_experiences_uuids
        ]

        professional_experiences_valuations = [
            AdmissionProfessionalValuatedExperiences(
                baseadmission_id=proposition.entity_id.uuid,
                professionalexperience_id=experience_uuid,
            )
            for experience_uuid in professional_experiences_uuids
        ]

        AdmissionEducationalValuatedExperiences.objects.bulk_create(educational_experiences_valuations)
        AdmissionProfessionalValuatedExperiences.objects.bulk_create(professional_experiences_valuations)

    @classmethod
    def decrocher(
        cls,
        proposition: Union[PropositionContinue, PropositionDoctorale, PropositionGenerale],
    ):
        if isinstance(
            proposition,
            (PropositionContinue, PropositionGenerale),
        ):
            BaseAdmission.objects.filter(uuid=proposition.entity_id.uuid).update(
                valuated_secondary_studies_person=None,
            )

        AdmissionEducationalValuatedExperiences.objects.filter(baseadmission_id=proposition.entity_id.uuid).delete()
        AdmissionProfessionalValuatedExperiences.objects.filter(baseadmission_id=proposition.entity_id.uuid).delete()
