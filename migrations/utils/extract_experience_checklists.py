# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
import itertools

import django.db.models.deletion
from django.db import migrations, models, transaction
from django.db.models import Q, Case, When, Value

from osis_profile.models.enums.experience_validation import EtatAuthentificationParcours, \
    ChoixStatutValidationExperience

def extract_experience_checklist(
    base_admission_model,
    secondary_studies_model,
    exam_model,
    educational_experience_model,
    professional_experience_model,
):
    valid_status = ChoixStatutValidationExperience.VALIDEE.name
    validated_experiences_uuids = set()
    candidates_ids_with_validated_secondary_studies = set()

    experiences_uuids_by_authentication_status = {}
    candidates_ids_by_authentication_status_secondary_studies = {}

    checklist_condition = Q(
        checklist__current__parcours_anterieur__enfants__contains=[{'statut': 'GEST_REUSSITE'}],
    )

    authentication_states_to_update = {
        EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
        EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name,
        EtatAuthentificationParcours.FAUX.name,
        EtatAuthentificationParcours.VRAI.name,
    }
    for authentication_state in authentication_states_to_update:
        checklist_condition |= Q(
            checklist__current__parcours_anterieur__enfants__contains=[{
                'extra': {'etat_authentification': authentication_state}
            }]
        )
        experiences_uuids_by_authentication_status[authentication_state] = set()
        candidates_ids_by_authentication_status_secondary_studies[authentication_state] = set()

    admissions = base_admission_model.objects.filter(checklist_condition).only('candidate_id', 'checklist')

    for admission in admissions:
        for experience_checklist in admission.checklist['current']['parcours_anterieur']['enfants']:
            if not experience_checklist.get('extra', {}).get('identifiant'):
                continue

            if experience_checklist['extra']['identifiant'] == 'ETUDES_SECONDAIRES':

                if experience_checklist.get('statut') == 'GEST_REUSSITE':
                    candidates_ids_with_validated_secondary_studies.add(admission.candidate_id)

                if experience_checklist['extra'].get('etat_authentification') in authentication_states_to_update:
                    candidates_ids_by_authentication_status_secondary_studies[experience_checklist['extra']['etat_authentification']].add(admission.candidate_id)

            else:
                if experience_checklist.get('statut') == 'GEST_REUSSITE':
                    validated_experiences_uuids.add(experience_checklist['extra']['identifiant'])

                if experience_checklist['extra'].get('etat_authentification') in authentication_states_to_update:
                    experiences_uuids_by_authentication_status[experience_checklist['extra']['etat_authentification']].add(experience_checklist['extra']['identifiant'])

    candidates_ids_with_authenticated_secondary_studies = set()
    authenticated_secondary_studies_conditions = []

    for status, person_ids in candidates_ids_by_authentication_status_secondary_studies.items():
        if person_ids:
            candidates_ids_with_authenticated_secondary_studies.update(person_ids)
            authenticated_secondary_studies_conditions.append(When(person_id__in=person_ids, then=Value(status)))

    authenticated_experiences_uuids = set()
    authenticated_experiences_conditions = []

    for status, experience_uuids in experiences_uuids_by_authentication_status.items():
        if experience_uuids:
            authenticated_experiences_uuids.update(experience_uuids)
            authenticated_experiences_conditions.append(When(uuid__in=experience_uuids, then=Value(status)))

    authenticated_experiences_case = Case(*authenticated_experiences_conditions)

    with transaction.atomic():
        secondary_studies_model.objects.filter(
            person_id__in=candidates_ids_with_validated_secondary_studies
        ).update(
            validation_status=valid_status
        )

        secondary_studies_model.objects.filter(
            person_id__in=candidates_ids_with_authenticated_secondary_studies
        ).update(
            authentication_status=Case(
                *authenticated_secondary_studies_conditions
            )
        )

        for model in [exam_model, educational_experience_model, professional_experience_model]:
            model.objects.filter(
                uuid__in=validated_experiences_uuids
            ).update(
                validation_status=valid_status
            )

            model.objects.filter(
                uuid__in=authenticated_experiences_uuids
            ).update(
                authentication_status=authenticated_experiences_case
            )
