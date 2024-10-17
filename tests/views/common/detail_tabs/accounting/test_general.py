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

import freezegun
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.models.general_education import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.enums import TypeSituationAssimilation, ChoixAffiliationSport, ChoixTypeCompteBancaire
from admission.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory, CandidateFactory
from base.models.enums.community import CommunityEnum
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2023-01-01')
class GeneralAccountingDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create data
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]
        cls.be_country = CountryFactory(iso_code='BE', name='Belgique', name_en='Belgium')
        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

    def setUp(self):
        # Create data
        self.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=self.first_doctoral_commission,
            training__academic_year=self.academic_years[0],
            candidate__language=settings.LANGUAGE_CODE_EN,
            candidate__country_of_citizenship=CountryFactory(european_union=False),
            candidate__graduated_from_high_school_year=None,
            candidate__last_registration_year=None,
            admitted=True,
        )

        # Create users
        self.sic_manager_user = SicManagementRoleFactory(entity=self.first_doctoral_commission).person.user
        self.program_manager_user = ProgramManagerRoleFactory(
            education_group=self.general_admission.training.education_group
        ).person.user

        # Targeted url
        self.url = resolve_url('admission:general-education:accounting', uuid=self.general_admission.uuid)

    def test_general_accounting_access(self):
        # If the user is not authenticated, they should be redirected to the login page
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, resolve_url('login') + '?next=' + self.url)

        # If the user is authenticated but doesn't have the right role, raise a 403
        self.client.force_login(CandidateFactory().person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # If the user is authenticated and has the right role, they should be able to access the page
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_general_accounting(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)
        self.assertEqual(response.context['formatted_relationship'], None)
        self.assertEqual(response.context['with_assimilation'], True)
        self.assertEqual(response.context['is_general'], True)

        accounting = response.context['accounting']
        self.assertEqual(accounting['demande_allocation_d_etudes_communaute_francaise_belgique'], False)
        self.assertEqual(accounting['enfant_personnel'], False)
        self.assertEqual(accounting['type_situation_assimilation'], TypeSituationAssimilation.AUCUNE_ASSIMILATION.name)
        self.assertEqual(accounting['affiliation_sport'], ChoixAffiliationSport.NON.name)
        self.assertEqual(accounting['etudiant_solidaire'], False)
        self.assertEqual(accounting['type_numero_compte'], ChoixTypeCompteBancaire.NON.name)

        self.assertEqual(accounting['derniers_etablissements_superieurs_communaute_fr_frequentes'], None)

    def test_get_general_accounting_with_frequented_fr_institutes(self):
        self.client.force_login(self.sic_manager_user)

        # Add educational experiences
        current_year = get_current_year()
        experiences = [
            # French community institute -> must be returned
            EducationalExperienceFactory(
                person=self.general_admission.candidate,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.FRENCH_SPEAKING.name,
                    acronym='INSTITUTE',
                    name='First institute',
                ),
            ),
            # UCL Louvain -> must be excluded
            EducationalExperienceFactory(
                person=self.general_admission.candidate,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.FRENCH_SPEAKING.name,
                    acronym=UCLouvain_acronym,
                    name='Second institute',
                ),
            ),
            # French community institute -> must be returned
            EducationalExperienceFactory(
                person=self.general_admission.candidate,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.FRENCH_SPEAKING.name,
                    acronym='INSTITUTE',
                    name='Third institute',
                ),
            ),
            # German community institute -> must be excluded
            EducationalExperienceFactory(
                person=self.general_admission.candidate,
                obtained_diploma=False,
                country=self.be_country,
                institute=OrganizationFactory(
                    community=CommunityEnum.GERMAN_SPEAKING.name,
                    acronym='INSTITUTE',
                    name='Fourth institute',
                ),
            ),
        ]
        for experience in experiences:
            EducationalExperienceYearFactory(
                educational_experience=experience,
                academic_year=AcademicYearFactory(year=current_year),
            )

        # French community institute but out of the range of require years -> must be excluded
        experience = EducationalExperienceFactory(
            person=self.general_admission.candidate,
            obtained_diploma=False,
            country=self.be_country,
            institute=OrganizationFactory(
                community=CommunityEnum.FRENCH_SPEAKING.name,
                acronym='INSTITUTE',
                name='Fifth institute',
            ),
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=AcademicYearFactory(year=current_year - 1),
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check context data
        self.assertEqual(response.context['admission'].uuid, self.general_admission.uuid)

        accounting = response.context['accounting']
        self.assertCountEqual(
            accounting['derniers_etablissements_superieurs_communaute_fr_frequentes']['names'],
            [
                'First institute',
                'Third institute',
            ],
        )
