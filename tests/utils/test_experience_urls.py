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
from django.test import TestCase

from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.test.factory.profil import (
    ExperienceAcademiqueDTOFactory,
    EtudesSecondairesDTOFactory,
    ExperienceNonAcademiqueDTOFactory,
    AnneeExperienceAcademiqueDTOFactory,
)
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory
from admission.utils import get_experience_urls
from base.models.person import Person
from base.tests.factories.user import UserFactory, SuperUserFactory


class ExperienceUrlsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.continuing_education = ContinuingEducationAdmissionFactory(
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )
        cls.user_who_can_edit_cv_and_profile = SuperUserFactory()
        cls.user_who_cannot_edit_cv_and_profile = UserFactory()
        cls.user_who_can_edit_cv_but_cannot_edit_profile = ProgramManagerRoleFactory(
            education_group=cls.continuing_education.training.education_group,
        ).person.user
        cls.candidate: Person = cls.continuing_education.candidate

    def test_get_urls_of_an_academic_experience_if_the_user_cannot_change_the_cv(self):
        academic_experience = ExperienceAcademiqueDTOFactory()

        experience_urls = get_experience_urls(
            user=self.user_who_cannot_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=academic_experience,
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/curriculum/educational/{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=academic_experience.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(experience_urls['edit_url'], '')
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(experience_urls['duplicate_url'], '')

    def test_get_urls_of_an_academic_experience_if_the_user_can_change_the_cv(self):
        academic_experience = ExperienceAcademiqueDTOFactory()

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=academic_experience,
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/curriculum/educational/{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=academic_experience.uuid,
            ),
        )
        self.assertEqual(
            experience_urls['delete_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/educational/'
            '{experience_uuid}/delete'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=academic_experience.uuid,
            ),
        )
        self.assertEqual(
            experience_urls['edit_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/educational/'
            '{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=academic_experience.uuid,
            ),
        )
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(
            experience_urls['duplicate_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/educational/'
            '{experience_uuid}/duplicate'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=academic_experience.uuid,
            ),
        )

    def test_get_urls_of_an_epc_academic_experience_if_the_user_can_change_the_cv(self):
        academic_experience = ExperienceAcademiqueDTOFactory(
            identifiant_externe='EPC1',
            annees=[AnneeExperienceAcademiqueDTOFactory()],
        )

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=academic_experience,
            candidate_noma='0123456789',
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/curriculum/educational/{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=academic_experience.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(
            experience_urls['edit_url'],
            '/osis_profile/0123456789/parcours_externe/edit/experience_academique/{experience_year_uuid}'.format(
                experience_year_uuid=academic_experience.annees[0].uuid,
            ),
        )
        self.assertEqual(experience_urls['edit_new_link_tab'], True)
        self.assertEqual(
            experience_urls['duplicate_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/educational/'
            '{experience_uuid}/duplicate'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=academic_experience.uuid,
            ),
        )

    def test_get_urls_of_an_epc_academic_experience_if_the_user_cannot_change_the_profile(self):
        academic_experience = ExperienceAcademiqueDTOFactory(
            identifiant_externe='EPC1',
            annees=[AnneeExperienceAcademiqueDTOFactory()],
        )

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_but_cannot_edit_profile,
            admission=self.continuing_education,
            experience=academic_experience,
            candidate_noma='0123456789',
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/curriculum/educational/{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=academic_experience.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(experience_urls['edit_url'], '')
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(
            experience_urls['duplicate_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/educational/'
            '{experience_uuid}/duplicate'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=academic_experience.uuid,
            ),
        )

    def test_get_urls_of_a_non_academic_experience_if_the_user_cannot_change_the_cv(self):
        non_academic_experience = ExperienceNonAcademiqueDTOFactory()

        experience_urls = get_experience_urls(
            user=self.user_who_cannot_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=non_academic_experience,
        )
        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/curriculum/non_educational/{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )

        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(experience_urls['edit_url'], '')
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(experience_urls['duplicate_url'], '')

    def test_get_urls_of_a_non_academic_experience_if_the_user_can_change_the_cv(self):
        non_academic_experience = ExperienceNonAcademiqueDTOFactory()

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=non_academic_experience,
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/curriculum/non_educational/{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )
        self.assertEqual(
            experience_urls['delete_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/non_educational/'
            '{experience_uuid}/delete'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )
        self.assertEqual(
            experience_urls['edit_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/non_educational/'
            '{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(
            experience_urls['duplicate_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/non_educational/'
            '{experience_uuid}/duplicate'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )

    def test_get_urls_of_an_epc_non_academic_experience_if_the_user_can_change_the_cv(self):
        non_academic_experience = ExperienceNonAcademiqueDTOFactory(
            identifiant_externe='EPC1',
        )

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=non_academic_experience,
            candidate_noma='0123456789',
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/curriculum/non_educational/{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(
            experience_urls['edit_url'],
            '/osis_profile/0123456789/parcours_externe/edit/experience_non_academique/{experience_uuid}'.format(
                experience_uuid=non_academic_experience.uuid,
            ),
        )
        self.assertEqual(experience_urls['edit_new_link_tab'], True)
        self.assertEqual(
            experience_urls['duplicate_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/non_educational/'
            '{experience_uuid}/duplicate'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )

    def test_get_urls_of_an_epc_non_academic_experience_if_the_user_can_change_the_cv_of_a_non_student_candidate(self):
        non_academic_experience = ExperienceNonAcademiqueDTOFactory(
            identifiant_externe='EPC1',
        )

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=non_academic_experience,
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/curriculum/non_educational/{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(experience_urls['edit_url'], '')
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(
            experience_urls['duplicate_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/non_educational/'
            '{experience_uuid}/duplicate'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )

    def test_get_urls_of_an_epc_non_academic_experience_if_the_user_cannot_change_the_profile(self):
        non_academic_experience = ExperienceNonAcademiqueDTOFactory(
            identifiant_externe='EPC1',
        )

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_but_cannot_edit_profile,
            admission=self.continuing_education,
            experience=non_academic_experience,
            candidate_noma='0123456789',
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/curriculum/non_educational/{experience_uuid}'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(experience_urls['edit_url'], '')
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(
            experience_urls['duplicate_url'],
            '/admissions/continuing-education/{admission_uuid}/update/curriculum/non_educational/'
            '{experience_uuid}/duplicate'.format(
                admission_uuid=self.continuing_education.uuid,
                experience_uuid=non_academic_experience.uuid,
            ),
        )

    def test_get_urls_of_the_secondary_studies_if_the_user_cannot_change_the_cv(self):
        secondary_studies = EtudesSecondairesDTOFactory()

        experience_urls = get_experience_urls(
            user=self.user_who_cannot_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=secondary_studies,
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/education'.format(
                admission_uuid=self.continuing_education.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(experience_urls['edit_url'], '')
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(experience_urls['duplicate_url'], '')

    def test_get_urls_of_the_secondary_studies_if_the_user_can_change_the_cv(self):
        secondary_studies = EtudesSecondairesDTOFactory()

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=secondary_studies,
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/education'.format(
                admission_uuid=self.continuing_education.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(
            experience_urls['edit_url'],
            '/admissions/continuing-education/{admission_uuid}/update/education'.format(
                admission_uuid=self.continuing_education.uuid,
            ),
        )
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(experience_urls['duplicate_url'], '')

    def test_get_urls_of_the_epc_secondary_studies_if_the_user_can_change_the_cv(self):
        secondary_studies = EtudesSecondairesDTOFactory(
            identifiant_externe='EPC1',
        )

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=secondary_studies,
            candidate_noma='0123456789',
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/education'.format(
                admission_uuid=self.continuing_education.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(
            experience_urls['edit_url'],
            '/osis_profile/0123456789/parcours_externe/edit/etudes_secondaires',
        )
        self.assertEqual(experience_urls['edit_new_link_tab'], True)
        self.assertEqual(experience_urls['duplicate_url'], '')

    def test_get_urls_of_the_epc_secondary_studies_if_the_user_can_change_the_cv_of_a_non_student_candidate(self):
        secondary_studies = EtudesSecondairesDTOFactory(
            identifiant_externe='EPC1',
        )

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_and_profile,
            admission=self.continuing_education,
            experience=secondary_studies,
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/education'.format(
                admission_uuid=self.continuing_education.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(experience_urls['edit_url'], '')
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(experience_urls['duplicate_url'], '')

    def test_get_urls_of_the_epc_secondary_studies_if_the_user_cannot_change_the_profile(self):
        secondary_studies = EtudesSecondairesDTOFactory(
            identifiant_externe='EPC1',
        )

        experience_urls = get_experience_urls(
            user=self.user_who_can_edit_cv_but_cannot_edit_profile,
            admission=self.continuing_education,
            experience=secondary_studies,
            candidate_noma='0123456789',
        )

        self.assertEqual(
            experience_urls['details_url'],
            '/admissions/continuing-education/{admission_uuid}/education'.format(
                admission_uuid=self.continuing_education.uuid,
            ),
        )
        self.assertEqual(experience_urls['delete_url'], '')
        self.assertEqual(experience_urls['edit_url'], '')
        self.assertEqual(experience_urls['edit_new_link_tab'], False)
        self.assertEqual(experience_urls['duplicate_url'], '')
