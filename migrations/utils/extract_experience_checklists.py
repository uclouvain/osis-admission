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
from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models, transaction
from django.db.models import Q, Case, When, Value, Exists, OuterRef, F, BooleanField, CharField
from django.db.models.expressions import RawSQL, Func
from django.db.models.functions import JSONObject

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.models.base import BaseAdmission
from admission.models.exam import AdmissionExam
from admission.models.valuated_epxeriences import AdmissionEducationalValuatedExperiences, \
    AdmissionProfessionalValuatedExperiences
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel
from osis_profile.models import EducationalExperience, ProfessionalExperience, BelgianHighSchoolDiploma, Exam, \
    ForeignHighSchoolDiploma, ExamType, EXAM_TYPE_PREMIER_CYCLE_LABEL_FR
from osis_profile.models.education import HighSchoolDiploma
from osis_profile.models.enums.experience_validation import EtatAuthentificationParcours, \
    ChoixStatutValidationExperience
from osis_profile.models.epc_injection import EPCInjection, ExperienceType

class JSONBPathExists(Func):
    function = "jsonb_path_exists"
    output_field = BooleanField()


checklist_valid_status = 'GEST_REUSSITE'
checklist_to_complete_after_enrolment_status = 'GEST_BLOCAGE_ULTERIEUR'

enrolment_valid_statuses = [
    EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
    EtatInscriptionFormation.PROVISOIRE.name,
    EtatInscriptionFormation.CESSATION.name,
]
json_experience_condition = '$.current.parcours_anterieur.enfants[*] ? (@.statut == $target_status && @.extra.identifiant == $experience_identifier)'


def in_draft_educational_experiences_qs(educational_experience_model, epc_injection_model, admission_educational_valuated_experiences_model, ):
    return educational_experience_model.objects.filter(
        external_id__isnull=True
    ).filter(
        ~Exists(epc_injection_model.objects.filter(experience_uuid=OuterRef('uuid'))),
        ~Exists(admission_educational_valuated_experiences_model.objects.filter(
            educationalexperience_id=OuterRef('uuid'),
        )),
    )

def validated_educational_experiences_qs(educational_experience_model, admission_educational_valuated_experiences_model, inscription_programme_annuel_model):
    return educational_experience_model.objects.exclude(
        validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name,
    ).annotate(
        valid_target_json=JSONObject(
            target_status=Value(checklist_valid_status),
            experience_identifier=F('uuid'),
        ),
        to_complete_after_enrolment_target_json=JSONObject(
            target_status=Value(checklist_to_complete_after_enrolment_status),
            experience_identifier=F('uuid'),
        )
    ).filter(
        Q(external_id__isnull=False)
        | Exists(
            admission_educational_valuated_experiences_model.objects.filter(
                educationalexperience_id=OuterRef('uuid'),
            ).filter(
                JSONBPathExists(
                    'baseadmission__checklist',
                    Value(json_experience_condition),
                    OuterRef('valid_target_json'),
                )
            )
        )
        | Exists(
            admission_educational_valuated_experiences_model.objects.filter(
                educationalexperience_id=OuterRef('uuid'),
            ).filter(
                JSONBPathExists(
                    'baseadmission__checklist',
                    Value(json_experience_condition),
                    OuterRef('to_complete_after_enrolment_target_json'),
                ),
                Exists(
                    inscription_programme_annuel_model.objects.filter(
                        admission_uuid=OuterRef('baseadmission_id'),
                        etat_inscription__in=enrolment_valid_statuses,
                    )
                )
            )
        )
    )

def in_draft_professional_experiences_qs(professional_experience_model, epc_injection_model, admission_professional_valuated_experiences_model):
    return professional_experience_model.objects.filter(
        external_id__isnull=True,
    ).filter(
        ~Exists(epc_injection_model.objects.filter(experience_uuid=OuterRef('uuid'))),
        ~Exists(admission_professional_valuated_experiences_model.objects.filter(
            professionalexperience_id=OuterRef('uuid'),
        )),
    )

def validated_professional_experiences_qs(professional_experience_model, admission_professional_valuated_experiences_model, inscription_programme_annuel_model):
    return professional_experience_model.objects.exclude(
        validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name,
    ).annotate(
        valid_target_json=JSONObject(
            target_status=Value(checklist_valid_status),
            experience_identifier=F('uuid'),
        ),
        to_complete_after_enrolment_target_json=JSONObject(
            target_status=Value(checklist_to_complete_after_enrolment_status),
            experience_identifier=F('uuid'),
        )
    ).filter(
        Q(external_id__isnull=False)
        | Exists(
            admission_professional_valuated_experiences_model.objects.filter(
                professionalexperience_id=OuterRef('uuid'),
            ).filter(
                JSONBPathExists(
                    'baseadmission__checklist',
                    Value(json_experience_condition),
                    OuterRef('valid_target_json'),
                )
            )
        ) | Exists(
            admission_professional_valuated_experiences_model.objects.filter(
                professionalexperience_id=OuterRef('uuid'),
            ).filter(
                JSONBPathExists(
                    'baseadmission__checklist',
                    Value(json_experience_condition),
                    OuterRef('valid_target_json'),
                ),
                Exists(inscription_programme_annuel_model.objects.filter(
                    admission_uuid=OuterRef('baseadmission_id'),
                    etat_inscription__in=enrolment_valid_statuses,
                )
                )
            )
        )
    )

def in_draft_secondary_studies_qs(secondary_studies_model, foreign_high_school_diploma_model, belgian_high_school_diploma_model, exam_model, epc_injection_model, base_admission_model, first_cycle_exam_type_id):
    return secondary_studies_model.objects.filter(
        ~Exists(foreign_high_school_diploma_model.objects.filter(person_id=OuterRef('person_id'), external_id__isnull=False, )),
        ~Exists(belgian_high_school_diploma_model.objects.filter(person_id=OuterRef('person_id'), external_id__isnull=False,)),
        ~Exists(exam_model.objects.filter(person_id=OuterRef('person_id'), external_id__isnull=False,
                                    type_id=first_cycle_exam_type_id,)),
        ~Exists(
            epc_injection_model.objects.filter(experience_uuid=OuterRef('uuid'), type_experience=ExperienceType.HIGH_SCHOOL,)),
        ~Exists(base_admission_model.objects.filter(valuated_secondary_studies_person_id=OuterRef('person_id'))),
    )

def validated_secondary_studies_qs(secondary_studies_model, foreign_high_school_diploma_model, belgian_high_school_diploma_model, exam_model, inscription_programme_annuel_model, base_admission_model, first_cycle_exam_type_id):
    return secondary_studies_model.objects.exclude(
        validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name,
    ).filter(
        Exists(foreign_high_school_diploma_model.objects.filter(person_id=OuterRef('person_id'), external_id__isnull=False))
        | Exists(belgian_high_school_diploma_model.objects.filter(person_id=OuterRef('person_id'), external_id__isnull=False))
        | Exists(exam_model.objects.filter(person_id=OuterRef('person_id'), external_id__isnull=False,
                                     type_id=first_cycle_exam_type_id,))
        | Exists(
            base_admission_model.objects.filter(
                candidate_id=OuterRef('person_id'),
                checklist__current__parcours_anterieur__enfants__contains=[{
                    'statut': checklist_valid_status, 'extra': {'identifiant': 'ETUDES_SECONDAIRES'}, }
                ],
            )
        )
        | Exists(
            base_admission_model.objects.filter(
                candidate_id=OuterRef('person_id'),
                checklist__current__parcours_anterieur__enfants__contains=[{
                    'statut': checklist_to_complete_after_enrolment_status,
                    'extra': {'identifiant': 'ETUDES_SECONDAIRES'},
                }],
            ).filter(
                Exists(inscription_programme_annuel_model.objects.filter(
                    admission_uuid=OuterRef('uuid'),
                    etat_inscription__in=enrolment_valid_statuses,
                )
                )
            )
        )
    )

def in_draft_exams_qs(exam_model, admission_exam_model, first_cycle_exam_type_id):
    return exam_model.objects.exclude(
        type_id=first_cycle_exam_type_id,
    ).filter(
        external_id__isnull=True,
    ).filter(
        Q(~Exists(admission_exam_model.objects.filter(exam_id=OuterRef('pk'))))
        | Q(~Exists(
            admission_exam_model.objects.filter(
                exam_id=OuterRef('pk'),
            ).filter(
                admission__generaleducationadmission__status__in=ChoixStatutPropositionGenerale.get_names_except(
        ChoixStatutPropositionGenerale.EN_BROUILLON.name,
        ChoixStatutPropositionGenerale.ANNULEE.name,
        ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,

    ))
            )
        )
    )

def validated_exams_qs(exam_model, admission_exam_model, first_cycle_exam_type_id):
    return exam_model.objects.exclude(
        type_id=first_cycle_exam_type_id,
        validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name,
    ).filter(
        Q(external_id__isnull=False) |
        Exists(admission_exam_model.objects.filter(
            exam_id=OuterRef('pk'),
            admission__generaleducationadmission__status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
        ))
    )


def authenticated_educational_experiences_qs(educational_experience_model, admission_educational_valuated_experiences_model, inscription_programme_annuel_model):
    return educational_experience_model.annotate(
        valid_target_json=JSONObject(
            target_authentication_status=Value(EtatAuthentificationParcours.NON_CONCERNE),
            experience_identifier=F('uuid'),
        ),
        to_complete_after_enrolment_target_json=JSONObject(
            target_authentication_status=Value(checklist_to_complete_after_enrolment_status),
            experience_identifier=F('uuid'),
        )
    ).filter(
        Q(external_id__isnull=False)
        | Exists(
            admission_educational_valuated_experiences_model.objects.filter(
                educationalexperience_id=OuterRef('uuid'),
            ).filter(
                JSONBPathExists(
                    'baseadmission__checklist',
                    Value(json_experience_condition),
                    OuterRef('valid_target_json'),
                )
            )
        )
        | Exists(
            admission_educational_valuated_experiences_model.objects.filter(
                educationalexperience_id=OuterRef('uuid'),
            ).filter(
                JSONBPathExists(
                    'baseadmission__checklist',
                    Value(json_experience_condition),
                    OuterRef('to_complete_after_enrolment_target_json'),
                ),
                Exists(
                    inscription_programme_annuel_model.objects.filter(
                        admission_uuid=OuterRef('baseadmission_id'),
                        etat_inscription__in=enrolment_valid_statuses,
                    )
                )
            )
        )
    )

@transaction.atomic
def extract_experience_checklist(
        base_admission_model,
        secondary_studies_model,
        exam_model,
        educational_experience_model,
        professional_experience_model,
        epc_injection_model,
        admission_educational_valuated_experiences_model,
        inscription_programme_annuel_model,
        admission_professional_valuated_experiences_model,
        foreign_high_school_diploma_model,
        belgian_high_school_diploma_model,
        admission_exam_model,
):
    first_cycle_exam_type_ids = ExamType.objects.filter(label_fr=EXAM_TYPE_PREMIER_CYCLE_LABEL_FR).values_list('pk',
                                                                                                                  flat=True)
    if len(first_cycle_exam_type_ids) != 1:
        raise 'One single exam type must exist for the first cycle exam'

    # Extract the checklist status
    in_draft_educational_experiences_qs(
        educational_experience_model=educational_experience_model,
        epc_injection_model=epc_injection_model,
        admission_educational_valuated_experiences_model=admission_educational_valuated_experiences_model,
    ).update(validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name)

    validated_educational_experiences_qs(
        educational_experience_model=educational_experience_model,
        admission_educational_valuated_experiences_model=admission_educational_valuated_experiences_model,
        inscription_programme_annuel_model=inscription_programme_annuel_model,
    ).update(validation_status=ChoixStatutValidationExperience.VALIDEE.name)

    in_draft_professional_experiences_qs(
        professional_experience_model=professional_experience_model,
        epc_injection_model=epc_injection_model,
        admission_professional_valuated_experiences_model=admission_professional_valuated_experiences_model,
    ).update(validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name)

    validated_professional_experiences_qs(
        professional_experience_model=professional_experience_model,
        admission_professional_valuated_experiences_model=admission_professional_valuated_experiences_model,
        inscription_programme_annuel_model=inscription_programme_annuel_model,
    ).update(validation_status=ChoixStatutValidationExperience.VALIDEE.name)

    in_draft_secondary_studies_qs(
        secondary_studies_model=secondary_studies_model,
        foreign_high_school_diploma_model=foreign_high_school_diploma_model,
        belgian_high_school_diploma_model=belgian_high_school_diploma_model,
        exam_model=exam_model,
        epc_injection_model=epc_injection_model,
        base_admission_model=base_admission_model,
        first_cycle_exam_type_id=first_cycle_exam_type_ids[0]
    ).update(validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name)

    validated_secondary_studies_qs(
        secondary_studies_model=secondary_studies_model,
        foreign_high_school_diploma_model=foreign_high_school_diploma_model,
        belgian_high_school_diploma_model=belgian_high_school_diploma_model,
        exam_model=exam_model,
        base_admission_model=base_admission_model,
        inscription_programme_annuel_model=inscription_programme_annuel_model,
        first_cycle_exam_type_id=first_cycle_exam_type_ids[0],
    ).update(validation_status=ChoixStatutValidationExperience.VALIDEE.name)

    in_draft_exams_qs(
        exam_model=exam_model,
        first_cycle_exam_type_id=first_cycle_exam_type_ids[0],
        admission_exam_model=admission_exam_model,
    ).update(validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name)

    validated_exams_qs(
        exam_model=exam_model,
        first_cycle_exam_type_id=first_cycle_exam_type_ids[0],
        admission_exam_model=admission_exam_model,
    ).update(validation_status=ChoixStatutValidationExperience.VALIDEE.name)

    # Extract the checklist authentication status
    experiences_uuids_by_authentication_status = {}
    candidates_ids_by_authentication_status_secondary_studies = {}

    checklist_condition = Q()

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

            if experience_checklist['extra'].get('etat_authentification') in authentication_states_to_update:
                if experience_checklist['extra']['identifiant'] == 'ETUDES_SECONDAIRES':
                    candidates_ids_by_authentication_status_secondary_studies[
                        experience_checklist['extra']['etat_authentification']].add(admission.candidate_id)
                else:
                    experiences_uuids_by_authentication_status[
                        experience_checklist['extra']['etat_authentification']].add(
                        experience_checklist['extra']['identifiant'])

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

    secondary_studies_model.objects.filter(
        person_id__in=candidates_ids_with_authenticated_secondary_studies
    ).update(
        authentication_status=Case(
            *authenticated_secondary_studies_conditions
        )
    )

    for model in [exam_model, educational_experience_model, professional_experience_model]:
        model.objects.filter(
            uuid__in=authenticated_experiences_uuids
        ).update(
            authentication_status=authenticated_experiences_case
        )
