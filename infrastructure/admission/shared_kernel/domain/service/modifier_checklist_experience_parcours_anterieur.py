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

from django.db import transaction
from django.db.models import QuerySet, Subquery

from admission.ddd.admission.shared_kernel.domain.service.i_modifier_checklist_experience_parcours_anterieur import \
    IValidationExperienceParcoursAnterieurService
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.ddd.admission.shared_kernel.dtos.validation_experience_parcours_anterieur import \
    ValidationExperienceParcoursAnterieurDTO
from admission.models.base import BaseAdmission
from admission.models.exam import AdmissionExam
from base.models.enums.got_diploma import GotDiploma
from base.models.person import Person
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from osis_profile.models import ProfessionalExperience, EducationalExperience, Exam, EXAM_TYPE_PREMIER_CYCLE_LABEL_FR, \
    ExamType
from osis_profile.models.education import HighSchoolDiploma
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition as PropositionDoctorale,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import (
    Proposition as PropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition as PropositionGenerale,
)
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


class ValidationExperienceParcoursAnterieurService(IValidationExperienceParcoursAnterieurService):
    @staticmethod
    def _get_professional_experience_qs(experience_uuid: str, global_id: str):
        return ProfessionalExperience.objects.filter(uuid=experience_uuid, person__global_id=global_id)

    @staticmethod
    def _get_educational_experience_qs(experience_uuid: str, global_id: str):
        return EducationalExperience.objects.filter(uuid=experience_uuid, person__global_id=global_id)

    @staticmethod
    def _get_exam_qs(experience_uuid: str, global_id: str):
        return Exam.objects.filter(uuid=experience_uuid, person__global_id=global_id)

    @staticmethod
    def _get_secondary_studies_qs(experience_uuid: str, global_id: str):
        return HighSchoolDiploma.objects.filter(uuid=experience_uuid, person__global_id=global_id)

    @classmethod
    def _get_experience_qs(
        cls,
        global_id: str,
        experience_uuid: str,
        experience_type: str,
    ) -> QuerySet[ProfessionalExperience|HighSchoolDiploma|EducationalExperience|Exam]:
        return {
            TypeExperience.ACTIVITE_NON_ACADEMIQUE.name: cls._get_professional_experience_qs,
            TypeExperience.ETUDES_SECONDAIRES.name: cls._get_secondary_studies_qs,
            TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name: cls._get_educational_experience_qs,
            TypeExperience.EXAMEN.name: cls._get_exam_qs,
        }[experience_type](experience_uuid=experience_uuid, global_id=global_id)

    @classmethod
    @transaction.atomic
    def _update_or_create_high_school_diploma(cls, global_id: str, data: dict):
        person_id = Person.objects.get(global_id=global_id).values_list('id', flat=True).first()

        high_school_diploma, created =  HighSchoolDiploma.objects.update_or_create(person_id=person_id, defaults=data)

        if high_school_diploma.got_diploma == GotDiploma.NO.name:
            Exam.objects.filter(
                type__label_fr=EXAM_TYPE_PREMIER_CYCLE_LABEL_FR,
                person_id=person_id,
            ).update(**data)

        return 1

    @classmethod
    @transaction.atomic
    def _update_or_create_exam(cls, experience_uuid: str, global_id: str, uuid_proposition: str, data: dict):
        if experience_uuid != TypeExperience.EXAMEN.name:
            return cls._get_exam_qs(experience_uuid=experience_uuid, global_id=global_id).update(**data)

        # else:
        admission: BaseAdmission = BaseAdmission.objects.get(uuid=uuid_proposition, candidate__global_id=global_id).select_related('exam__exam')

        exam_type = ExamType.objects.filter(education_group_years__id=admission.training_id).first()

        if exam_type is None:
            return 0

        if hasattr(admission, 'exam'):
            for field, field_value in data:
                setattr(admission.exam.exam, field, field_value)

            admission.exam.exam.save(update_fields=data.keys())

            return 1

        exam = Exam.objects.create(
            person_id=admission.candidate_id,
            type=exam_type,
            **data,
        )

        admission_exam = AdmissionExam.objects.create(admission=admission, exam=exam)

        return 1

    @classmethod
    def _update_experience(cls, experience_type: str, proposition_uuid: str, experience_uuid: str, global_id: str, **data,):
        if experience_type == TypeExperience.ETUDES_SECONDAIRES.name:
            updates_number = cls._update_or_create_high_school_diploma(global_id=global_id, data=data)
        elif experience_type == TypeExperience.EXAMEN.name:
            updates_number = cls._update_or_create_exam(
                experience_uuid=experience_uuid,
                global_id=global_id,
                proposition_uuid=proposition_uuid,
                data=data,
            )
        else:
            updates_number = cls._get_experience_qs(
                global_id=global_id,
                experience_uuid=experience_uuid,
                experience_type=experience_type,
            ).update(**data)

        if not updates_number:
            raise ExperienceNonTrouveeException

    @classmethod
    def modifier_statut(
        cls,
        matricule_candidat: str,
        uuid_proposition: str,
        uuid_experience: str,
        type_experience: str,
        statut: str,
    ):
        cls._update_experience(
            global_id=matricule_candidat,
            proposition_uuid=uuid_proposition,
            experience_uuid=uuid_experience,
            experience_type=type_experience,
            validation_status=statut,
        )

    @classmethod
    def modifier_authentification(
        cls,
        matricule_candidat: str,
        uuid_proposition: str,
        uuid_experience: str,
        type_experience: str,
        etat_authentification: str,
    ):
        cls._update_experience(
            global_id=matricule_candidat,
            experience_uuid=uuid_experience,
            experience_type=type_experience,
            authentication_status=etat_authentification,
        )

    @classmethod
    def recuperer_information_validation(
        cls,
        matricule_candidat: str,
        uuid_experience: str,
        type_experience: str,
    ):
        experience = cls._get_experience_qs(
            global_id=matricule_candidat,
            experience_uuid=uuid_experience,
            experience_type=type_experience,
        ).values(
            'validation_status',
            'authentication_status',
        ).first()

        if not experience:
            raise ExperienceNonTrouveeException

        return ValidationExperienceParcoursAnterieurDTO(
            uuid=uuid_experience,
            type_experience=type_experience,
            statut_validation=experience['validation_status'],
            statut_authentification=experience['authentication_status'],
        )

    @classmethod
    @transaction.atomic
    def mettre_a_jour_experiences_en_brouillon(
        cls,
        proposition: PropositionContinue | PropositionDoctorale | PropositionGenerale,
    ):
        in_draft_status = ChoixStatutValidationExperience.EN_BROUILLON.name
        to_be_processed_status = ChoixStatutValidationExperience.A_TRAITER.name

        candidate_id = Person.objects.filter(global_id=proposition.matricule_candidat).values_list('pk', flat=True).get()

        if isinstance(proposition, (PropositionContinue, PropositionGenerale)):
            # In the rare case where the highschooldiploma is not specified, we create it here
            high_school_diploma, created = HighSchoolDiploma.objects.get_or_create(person_id=candidate_id)

            if high_school_diploma.validation_status == in_draft_status:
                high_school_diploma.objects.filter(pk=high_school_diploma.pk).update(validation_status=to_be_processed_status)

            if high_school_diploma.got_diploma == GotDiploma.NO.name:
                Exam.objects.filter(
                    type__label_fr=EXAM_TYPE_PREMIER_CYCLE_LABEL_FR,
                    person_id=candidate_id,
                    validation_status=in_draft_status
                ).update(
                    validation_status=to_be_processed_status
                )

        if isinstance(proposition, PropositionGenerale):
            Exam.objects.filter(
                person_id=candidate_id,
                admissions__admission__uuid=proposition.entity_id.uuid,
                validation_status=in_draft_status
            ).update(validation_status=to_be_processed_status)

        EducationalExperience.objects.filter(
            person_id=candidate_id,
            validation_status=in_draft_status
        ).update(
            validation_status=to_be_processed_status
        )

        ProfessionalExperience.objects.filter(
            person_id=candidate_id,
            validation_status=in_draft_status
        ).update(validation_status=to_be_processed_status)

