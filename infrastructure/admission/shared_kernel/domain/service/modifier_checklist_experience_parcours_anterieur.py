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

from django.db import transaction
from django.db.models import Q

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition as PropositionDoctorale,
    PropositionIdentity,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition as PropositionContinue
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGenerale
from admission.ddd.admission.shared_kernel.domain.service.i_modifier_checklist_experience_parcours_anterieur import (
    IValidationExperienceParcoursAnterieurService,
)
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import AdmissionExperienceNonTrouveeException
from osis_profile.models import EXAM_TYPE_PREMIER_CYCLE_LABEL_FR, EducationalExperience, Exam, ProfessionalExperience
from osis_profile.models.education import HighSchoolDiploma
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


class ValidationExperienceParcoursAnterieurService(IValidationExperienceParcoursAnterieurService):
    @staticmethod
    def _get_educational_experience_qs(experience_uuid: str):
        return EducationalExperience.objects.filter(uuid=experience_uuid)

    @classmethod
    def modifier_statut_experience_academique(
        cls,
        uuid_experience: str,
        statut: str,
        profil_candidat_translator: IProfilCandidatTranslator,
        proposition_id: PropositionIdentity = None,
        matricule_candidat: str = None,
        grade_academique_formation_proposition: str = None,
    ):
        super().modifier_statut_experience_academique(
            proposition_id=proposition_id,
            matricule_candidat=matricule_candidat,
            uuid_experience=uuid_experience,
            statut=statut,
            profil_candidat_translator=profil_candidat_translator,
            grade_academique_formation_proposition=grade_academique_formation_proposition,
        )

        updates_number = cls._get_educational_experience_qs(experience_uuid=uuid_experience).update(
            validation_status=statut
        )

        if not updates_number:
            raise AdmissionExperienceNonTrouveeException

    @classmethod
    def modifier_authentification_experience_academique(cls, uuid_experience: str, etat_authentification: str):
        updates_number = cls._get_educational_experience_qs(experience_uuid=uuid_experience).update(
            authentication_status=etat_authentification
        )

        if not updates_number:
            raise AdmissionExperienceNonTrouveeException

    @staticmethod
    def _get_professional_experience_qs(experience_uuid: str):
        return ProfessionalExperience.objects.filter(uuid=experience_uuid)

    @classmethod
    def modifier_authentification_experience_non_academique(cls, uuid_experience: str, etat_authentification: str):
        updates_number = cls._get_professional_experience_qs(experience_uuid=uuid_experience).update(
            authentication_status=etat_authentification
        )

        if not updates_number:
            raise AdmissionExperienceNonTrouveeException

    @staticmethod
    def _get_secondary_studies_qs(experience_uuid: str):
        return HighSchoolDiploma.objects.filter(uuid=experience_uuid)

    @classmethod
    @transaction.atomic
    def modifier_authentification_etudes_secondaires(
        cls,
        uuid_experience: str,
        etat_authentification: str,
    ):
        updates_number = cls._get_secondary_studies_qs(experience_uuid=uuid_experience).update(
            authentication_status=etat_authentification
        )

        if not updates_number:
            raise AdmissionExperienceNonTrouveeException

        Exam.objects.filter(
            type__label_fr=EXAM_TYPE_PREMIER_CYCLE_LABEL_FR,
            person__highschooldiploma__uuid=uuid_experience,
        ).update(validation_status=etat_authentification)

    @staticmethod
    def _get_exam_qs(experience_uuid: str):
        return Exam.objects.filter(uuid=experience_uuid)

    @classmethod
    def modifier_statut_examen(
        cls,
        proposition_id,
        sigle_formation: str,
        annee_formation: int,
        matricule_candidat: str,
        uuid_experience: str,
        statut: str,
        profil_candidat_translator: IProfilCandidatTranslator,
    ):
        super().modifier_statut_examen(
            proposition_id=proposition_id,
            sigle_formation=sigle_formation,
            annee_formation=annee_formation,
            matricule_candidat=matricule_candidat,
            uuid_experience=uuid_experience,
            statut=statut,
            profil_candidat_translator=profil_candidat_translator,
        )

        updates_number = cls._get_exam_qs(experience_uuid=uuid_experience).update(validation_status=statut)

        if not updates_number:
            raise AdmissionExperienceNonTrouveeException

    @classmethod
    def modifier_authentification_examen(
        cls,
        uuid_experience: str,
        etat_authentification: str,
    ):
        updates_number = cls._get_exam_qs(experience_uuid=uuid_experience).update(
            authentication_status=etat_authentification
        )

        if not updates_number:
            raise AdmissionExperienceNonTrouveeException

    @classmethod
    @transaction.atomic
    def passer_experiences_en_brouillon_en_a_traiter(
        cls,
        proposition: PropositionContinue | PropositionDoctorale | PropositionGenerale,
    ):
        in_draft_status = ChoixStatutValidationExperience.EN_BROUILLON.name
        to_be_processed_status = ChoixStatutValidationExperience.A_TRAITER.name

        exams_conditions = Q()

        if isinstance(proposition, (PropositionContinue, PropositionGenerale)):
            HighSchoolDiploma.objects.filter(
                person__global_id=proposition.matricule_candidat,
                validation_status=in_draft_status,
            ).update(validation_status=to_be_processed_status)

            exams_conditions |= Q(type__label_fr=EXAM_TYPE_PREMIER_CYCLE_LABEL_FR)

        if isinstance(proposition, PropositionGenerale):
            exams_conditions |= Q(admissions__admission__uuid=proposition.entity_id.uuid)

        if exams_conditions:
            Exam.objects.filter(
                exams_conditions,
                person__global_id=proposition.matricule_candidat,
                validation_status=in_draft_status,
            ).update(validation_status=to_be_processed_status)

        EducationalExperience.objects.filter(
            person__global_id=proposition.matricule_candidat,
            validation_status=in_draft_status,
            educational_valuated_experiences__baseadmission_id=proposition.entity_id.uuid,
        ).update(validation_status=to_be_processed_status)

        ProfessionalExperience.objects.filter(
            person__global_id=proposition.matricule_candidat,
            validation_status=in_draft_status,
            professional_valuated_experiences__baseadmission_id=proposition.entity_id.uuid,
        ).update(validation_status=to_be_processed_status)
