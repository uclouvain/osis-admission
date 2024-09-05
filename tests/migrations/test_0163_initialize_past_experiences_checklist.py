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
import uuid

from django.test import TestCase

from admission.models.base import BaseAdmission
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.migrations.utils.initialize_past_experiences_checklist import (
    initialization_of_missing_checklists_in_cv_experiences,
)
from admission.tests.factories.curriculum import (
    EducationalExperienceFactory,
    AdmissionEducationalValuatedExperiencesFactory,
    ProfessionalExperienceFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory


class InitializePastExperiencesChecklistTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.default_checklist = {
            'current': {
                'parcours_anterieur': {
                    'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                    'enfants': [],
                },
            },
        }
        cls.default_secondary_studies_checklist = cls._get_default_experience_checklist(
            OngletsDemande.ETUDES_SECONDAIRES.name,
        )

    @classmethod
    def _get_default_experience_checklist(cls, experience_uuid):
        return {
            'libelle': 'To be processed',
            'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
            'extra': {
                'identifiant': experience_uuid,
                'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
            },
            'enfants': [],
        }

    def test_initialization_is_not_needed_if_the_proposition_has_not_been_submitted(self):
        # In progress
        admission = GeneralEducationAdmissionFactory(
            checklist=self.default_checklist,
            status=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
        )

        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        self.assertEqual(admission.checklist, self.default_checklist)

    def test_initialization_is_not_needed_if_the_proposition_checklist_past_experiences_tab_is_not_initialized(self):
        admission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        for checklist_value in [
            {},
            {'current': {}},
            {'current__parcours_anterieur': {}},
        ]:
            admission.checklist = checklist_value
            admission.save(update_fields=['checklist'])
            initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)
            admission.refresh_from_db()

            self.assertEqual(admission.checklist, checklist_value, checklist_value)

    def test_initialization_of_the_secondary_studies(self):
        admission = GeneralEducationAdmissionFactory(
            checklist=self.default_checklist,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # The checklist is not yet initialized -> initialization of the checklist of the secondary studies
        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        experiences = admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences), 1)
        self.assertIn(self.default_secondary_studies_checklist, experiences)

        # The checklist of the secondary studies is already initialized -> no update
        updated_secondary_studies_checklist = experiences[0]

        updated_secondary_studies_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        updated_secondary_studies_checklist['extra'][
            'etat_authentification'
        ] = EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name
        updated_secondary_studies_checklist['extra']['custom-param'] = '1'

        admission.save(update_fields=['checklist'])

        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        experiences = admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences), 1)
        self.assertIn(updated_secondary_studies_checklist, experiences)

        # The checklist of another experience is already initialized -> no update of the existing one but
        # initialization of the checklist of the secondary studies
        another_uuid = str(uuid.uuid4())
        other_experience_checklist = experiences[0]
        other_experience_checklist['extra']['identifiant'] = another_uuid

        admission.save(update_fields=['checklist'])

        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        experiences = admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences), 2)
        self.assertIn(self.default_secondary_studies_checklist, experiences)
        self.assertIn(other_experience_checklist, experiences)

    def test_initialization_of_the_educational_experiences(self):
        admission = GeneralEducationAdmissionFactory(
            checklist=self.default_checklist,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        educational_experience = EducationalExperienceFactory(person=admission.candidate)
        no_valuated_educational_experience = EducationalExperienceFactory(person=admission.candidate)

        educational_experience_uuid = str(educational_experience.uuid)

        educational_experience_default_checklist = self._get_default_experience_checklist(
            experience_uuid=educational_experience_uuid,
        )

        valuated_educational_experience = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=admission,
            educationalexperience=educational_experience,
        )

        # The checklist is not yet initialized -> initialization of the checklists of the experience and of the
        # secondary studies
        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        experiences = admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences), 2)
        self.assertIn(self.default_secondary_studies_checklist, experiences)
        self.assertIn(educational_experience_default_checklist, experiences)

        # The checklist of the educational experience is already initialized -> no update
        educational_experience_updated_checklist = next(
            experience_checklist
            for experience_checklist in experiences
            if experience_checklist['extra']['identifiant'] == educational_experience_uuid
        )
        educational_experience_updated_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        educational_experience_updated_checklist['extra'][
            'etat_authentification'
        ] = EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name
        educational_experience_updated_checklist['extra']['custom-param'] = '1'

        admission.save(update_fields=['checklist'])

        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        experiences = admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences), 2)
        self.assertIn(self.default_secondary_studies_checklist, experiences)
        self.assertIn(educational_experience_updated_checklist, experiences)

        # The checklist of another experiences are already initialized -> no update of the existing ones but
        # initialization of the missing one
        other_experience_checklist = next(
            experience_checklist
            for experience_checklist in experiences
            if experience_checklist['extra']['identifiant'] == educational_experience_uuid
        )
        other_experience_checklist['extra']['identifiant'] = str(no_valuated_educational_experience.uuid)

        admission.save(update_fields=['checklist'])

        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        experiences = admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences), 3)
        self.assertIn(self.default_secondary_studies_checklist, experiences)
        self.assertIn(other_experience_checklist, experiences)
        self.assertIn(educational_experience_default_checklist, experiences)

    def test_initialization_of_the_non_professional_experiences(self):
        admission = GeneralEducationAdmissionFactory(
            checklist=self.default_checklist,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        professional_experience = ProfessionalExperienceFactory(person=admission.candidate)
        no_valuated_professional_experience = ProfessionalExperienceFactory(person=admission.candidate)

        professional_experience_uuid = str(professional_experience.uuid)

        professional_experience_default_checklist = self._get_default_experience_checklist(
            experience_uuid=professional_experience_uuid,
        )

        valuated_professional_experience = AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=admission,
            professionalexperience=professional_experience,
        )

        # The checklist is not yet initialized -> initialization of the checklists of the experience and of the
        # secondary studies
        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        experiences = admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences), 2)
        self.assertIn(self.default_secondary_studies_checklist, experiences)
        self.assertIn(professional_experience_default_checklist, experiences)

        # The checklist of the educational experience is already initialized -> no update
        professional_experience_updated_checklist = next(
            experience_checklist
            for experience_checklist in experiences
            if experience_checklist['extra']['identifiant'] == professional_experience_uuid
        )
        professional_experience_updated_checklist['statut'] = ChoixStatutChecklist.GEST_REUSSITE.name
        professional_experience_updated_checklist['extra'][
            'etat_authentification'
        ] = EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name
        professional_experience_updated_checklist['extra']['custom-param'] = '1'

        admission.save(update_fields=['checklist'])

        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        experiences = admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences), 2)
        self.assertIn(self.default_secondary_studies_checklist, experiences)
        self.assertIn(professional_experience_updated_checklist, experiences)

        # The checklist of another experiences are already initialized -> no update of the existing ones but
        # initialization of the missing one
        other_experience_checklist = next(
            experience_checklist
            for experience_checklist in experiences
            if experience_checklist['extra']['identifiant'] == professional_experience_uuid
        )
        other_experience_checklist['extra']['identifiant'] = str(no_valuated_professional_experience.uuid)

        admission.save(update_fields=['checklist'])

        initialization_of_missing_checklists_in_cv_experiences(BaseAdmission)

        admission.refresh_from_db()

        experiences = admission.checklist['current']['parcours_anterieur']['enfants']

        self.assertEqual(len(experiences), 3)
        self.assertIn(self.default_secondary_studies_checklist, experiences)
        self.assertIn(other_experience_checklist, experiences)
        self.assertIn(professional_experience_default_checklist, experiences)
