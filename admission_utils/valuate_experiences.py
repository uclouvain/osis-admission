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

from admission.models import GeneralEducationAdmission, ContinuingEducationAdmission, DoctorateAdmission
from osis_profile.models import EducationalExperience, ProfessionalExperience


def valuate_experiences(instance: Union[GeneralEducationAdmission, ContinuingEducationAdmission, DoctorateAdmission]):
    # Valuate the secondary studies of the candidate
    if isinstance(
        instance,
        (GeneralEducationAdmission, ContinuingEducationAdmission),
    ):
        instance.valuated_secondary_studies_person_id = instance.candidate_id
        instance.save(update_fields=['valuated_secondary_studies_person_id'])

    # Valuate curriculum experiences
    instance.educational_valuated_experiences.add(
        *EducationalExperience.objects.filter(person_id=instance.candidate_id)
    )

    # Valuate curriculum experiences
    instance.professional_valuated_experiences.add(
        *ProfessionalExperience.objects.filter(person_id=instance.candidate_id)
    )
