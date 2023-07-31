# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.test.factory.profil import EtudesSecondairesDTOFactory, ExperienceNonAcademiqueDTOFactory, \
    ExperienceAcademiqueDTOFactory, AnneeExperienceAcademiqueDTOFactory
from admission.templatetags.admission_parcours import get_experience_last_year, get_experience_year, \
    filter_experiences_trainings, filter_experiences_financability
from admission.tests import TestCase


class AdmissionParcoursFiltersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.derniere_annee = AnneeExperienceAcademiqueDTOFactory(annee=2021)
        cls.annee_2020 = AnneeExperienceAcademiqueDTOFactory(annee=2020)
        cls.experience_academique = ExperienceAcademiqueDTOFactory(
            annees=[
                cls.annee_2020,
                AnneeExperienceAcademiqueDTOFactory(annee=2018),
                cls.derniere_annee,
                AnneeExperienceAcademiqueDTOFactory(annee=2019),
            ]
        )
        cls.etudes_secondaires = EtudesSecondairesDTOFactory()
        cls.experiences = {
            2017: [
                ExperienceNonAcademiqueDTOFactory(),
            ],
            2018: [
                cls.etudes_secondaires,
                ExperienceNonAcademiqueDTOFactory(),
            ],
            2020: [
                ExperienceNonAcademiqueDTOFactory(),
            ],
            2021: [
                cls.experience_academique,
            ],
            2022: [
                ExperienceNonAcademiqueDTOFactory(),
            ]
        }

    def test_get_experience_last_year(self):
        self.assertEqual(get_experience_last_year(self.experience_academique), self.derniere_annee.annee)

    def test_get_experience_year(self):
        self.assertEqual(get_experience_year(self.experience_academique, 2020), self.annee_2020)

    def test_filter_experiences_trainings(self):
        experiences = filter_experiences_trainings(self.experiences)
        self.assertEqual(len(experiences), 4)
        self.assertFalse(experiences[2019])
        self.assertFalse(experiences[2020])

    def test_filter_experiences_financability(self):
        experiences = filter_experiences_financability(self.experiences)
        self.assertEqual(len(experiences), 5)
        self.assertEqual(len(experiences[2018]), 1)
        self.assertEqual(experiences[2018][0], self.etudes_secondaires)
