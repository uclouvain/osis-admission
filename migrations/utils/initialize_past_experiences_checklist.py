# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from copy import deepcopy

from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    STATUTS_PROPOSITION_GENERALE_NON_SOUMISE,
    OngletsChecklist,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist


def initialization_of_missing_checklists_in_cv_experiences(admission_model_class):
    """
    Some admissions have been submitted before the development of the checklist for the cv experiences so we
    need to initialize the checklist of each valuated experience.
    """

    admissions = (
        admission_model_class.objects.filter(
            checklist__current__parcours_anterieur__has_key='enfants',
        )
        .exclude(generaleducationadmission__status__in=STATUTS_PROPOSITION_GENERALE_NON_SOUMISE)
        .prefetch_related(
            'admissioneducationalvaluatedexperiences_set',
            'admissionprofessionalvaluatedexperiences_set',
        )
    )

    default_checklist = Checklist.initialiser_checklist_experience(experience_uuid='EXPERIENCE_UUID_TO_INIT').to_dict()

    current_tab = OngletsChecklist.parcours_anterieur.name

    admissions_to_update = []

    for current_admission in admissions:
        need_update = False

        if current_admission.checklist and 'enfants' in current_admission.checklist.get('current', {}).get(
            current_tab,
            {},
        ):

            current_children = current_admission.checklist['current'][current_tab]['enfants']
            current_children_uuids = set(
                [child['extra']['identifiant'] for child in current_children if child['extra'].get('identifiant')]
            )

            # Add the educational experiences
            for admission_valuated_experience in current_admission.admissioneducationalvaluatedexperiences_set.all():
                current_uuid = str(admission_valuated_experience.educationalexperience_id)

                if current_uuid not in current_children_uuids:
                    need_update = True
                    current_checklist = deepcopy(default_checklist)
                    current_checklist['extra']['identifiant'] = current_uuid
                    current_children.append(current_checklist)

            # Add the professional experiences
            for admission_valuated_experience in current_admission.admissionprofessionalvaluatedexperiences_set.all():
                current_uuid = str(admission_valuated_experience.professionalexperience_id)

                if current_uuid not in current_children_uuids:
                    need_update = True
                    current_checklist = deepcopy(default_checklist)
                    current_checklist['extra']['identifiant'] = current_uuid
                    current_children.append(current_checklist)

            # Add the secondary studies experience
            current_uuid = OngletsDemande.ETUDES_SECONDAIRES.name

            if current_uuid not in current_children_uuids:
                need_update = True
                current_checklist = deepcopy(default_checklist)
                current_checklist['extra']['identifiant'] = current_uuid
                current_children.append(current_checklist)

            if need_update:
                admissions_to_update.append(current_admission)

    admission_model_class.objects.bulk_update(admissions_to_update, ['checklist'], batch_size=500)
