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
import uuid

from django.test import TestCase

from admission.ddd.admission.shared_kernel.commands import \
    RecupererInformationsValidationExperienceParcoursAnterieurQuery
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.ddd.admission.shared_kernel.dtos.validation_experience_parcours_anterieur import \
    ValidationExperienceParcoursAnterieurDTO
from admission.tests.factories.curriculum import EducationalExperienceFactory, ProfessionalExperienceFactory
from base.models.person import Person
from base.tests.factories.person import PersonFactory
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from infrastructure.messages_bus import message_bus_instance
from osis_profile.models import EducationalExperience, ProfessionalExperience, Exam
from osis_profile.models.education import HighSchoolDiploma
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience, \
    EtatAuthentificationParcours
from osis_profile.tests.factories.exam import ExamFactory
from osis_profile.tests.factories.high_school_diploma import HighSchoolDiplomaFactory


class RecupererInformationsValidationExperienceParcoursAnterieurTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.personne: Person = PersonFactory()

    def test_lever_exception_si_uuid_experience_non_reconnu(self):
        with self.assertRaises(ExperienceNonTrouveeException):
            message_bus_instance.invoke(
                RecupererInformationsValidationExperienceParcoursAnterieurQuery(
                    uuid_experience=str(uuid.uuid4()),
                    type_experience=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
                    matricule_candidat=self.personne.global_id,
                )
            )

    def test_lever_exception_si_type_experience_non_conforme(self):
        experience: EducationalExperience = EducationalExperienceFactory(
            person=self.personne,
            validation_status=ChoixStatutValidationExperience.AVIS_EXPERT.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        with self.assertRaises(ExperienceNonTrouveeException):
            message_bus_instance.invoke(
                RecupererInformationsValidationExperienceParcoursAnterieurQuery(
                    uuid_experience=str(experience.uuid),
                    type_experience=TypeExperience.ACTIVITE_NON_ACADEMIQUE.name,
                    matricule_candidat=self.personne.global_id,
                )
            )

    def test_lever_exception_si_matricule_candidat_non_conforme(self):
        experience: EducationalExperience = EducationalExperienceFactory(
            person=self.personne,
            validation_status=ChoixStatutValidationExperience.AVIS_EXPERT.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        with self.assertRaises(ExperienceNonTrouveeException):
            message_bus_instance.invoke(
                RecupererInformationsValidationExperienceParcoursAnterieurQuery(
                    uuid_experience=str(experience.uuid),
                    type_experience=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
                    matricule_candidat='INCONNU',
                )
            )

    def test_recuperer_informations_experience_academique(self):
        experience: EducationalExperience = EducationalExperienceFactory(
            person=self.personne,
            validation_status=ChoixStatutValidationExperience.AVIS_EXPERT.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        experience_dto: ValidationExperienceParcoursAnterieurDTO = message_bus_instance.invoke(
            RecupererInformationsValidationExperienceParcoursAnterieurQuery(
                uuid_experience=str(experience.uuid),
                type_experience=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
                matricule_candidat=self.personne.global_id,
            )
        )

        self.assertEqual(experience_dto.uuid, str(experience.uuid))
        self.assertEqual(experience_dto.type_experience, TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name)
        self.assertEqual(experience_dto.statut_validation, ChoixStatutValidationExperience.AVIS_EXPERT.name)
        self.assertEqual(experience_dto.statut_authentification, EtatAuthentificationParcours.VRAI.name)


    def test_recuperer_informations_experience_non_academique(self):
        experience: ProfessionalExperience = ProfessionalExperienceFactory(
            person=self.personne,
            validation_status=ChoixStatutValidationExperience.AVIS_EXPERT.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        experience_dto: ValidationExperienceParcoursAnterieurDTO = message_bus_instance.invoke(
            RecupererInformationsValidationExperienceParcoursAnterieurQuery(
                uuid_experience=str(experience.uuid),
                type_experience=TypeExperience.ACTIVITE_NON_ACADEMIQUE.name,
                matricule_candidat=self.personne.global_id,
            )
        )

        self.assertEqual(experience_dto.uuid, str(experience.uuid))
        self.assertEqual(experience_dto.type_experience, TypeExperience.ACTIVITE_NON_ACADEMIQUE.name)
        self.assertEqual(experience_dto.statut_validation, ChoixStatutValidationExperience.AVIS_EXPERT.name)
        self.assertEqual(experience_dto.statut_authentification, EtatAuthentificationParcours.VRAI.name)



    def test_recuperer_informations_examen(self):
        experience: Exam = ExamFactory(
            person=self.personne,
            validation_status=ChoixStatutValidationExperience.AVIS_EXPERT.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        experience_dto: ValidationExperienceParcoursAnterieurDTO = message_bus_instance.invoke(
            RecupererInformationsValidationExperienceParcoursAnterieurQuery(
                uuid_experience=str(experience.uuid),
                type_experience=TypeExperience.EXAMEN.name,
                matricule_candidat=self.personne.global_id,
            )
        )

        self.assertEqual(experience_dto.uuid, str(experience.uuid))
        self.assertEqual(experience_dto.type_experience, TypeExperience.EXAMEN.name)
        self.assertEqual(experience_dto.statut_validation, ChoixStatutValidationExperience.AVIS_EXPERT.name)
        self.assertEqual(experience_dto.statut_authentification, EtatAuthentificationParcours.VRAI.name)



    def test_recuperer_informations_etudes_secondaires(self):
        experience: HighSchoolDiploma = HighSchoolDiplomaFactory(
            person=self.personne,
            validation_status=ChoixStatutValidationExperience.AVIS_EXPERT.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        experience_dto: ValidationExperienceParcoursAnterieurDTO = message_bus_instance.invoke(
            RecupererInformationsValidationExperienceParcoursAnterieurQuery(
                uuid_experience=str(experience.uuid),
                type_experience=TypeExperience.ETUDES_SECONDAIRES.name,
                matricule_candidat=self.personne.global_id,
            )
        )

        self.assertEqual(experience_dto.uuid, str(experience.uuid))
        self.assertEqual(experience_dto.type_experience, TypeExperience.ETUDES_SECONDAIRES.name)
        self.assertEqual(experience_dto.statut_validation, ChoixStatutValidationExperience.AVIS_EXPERT.name)
        self.assertEqual(experience_dto.statut_authentification, EtatAuthentificationParcours.VRAI.name)

