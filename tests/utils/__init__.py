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

from admission.ddd.admission.domain.model.enums.condition_acces import TypeTitreAccesSelectionnable
from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from admission.utils import access_title_country


class UtilsTestCase(TestCase):
    def test_access_title_country(self):
        uuid_experience = str(uuid.uuid4())

        # With no access title
        self.assertEqual(access_title_country({}), '')

        # With not selected access titles
        access_titles = [
            TitreAccesSelectionnableDTO(
                type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name,
                selectionne=False,
                uuid_experience=uuid_experience,
                annee=None,
                pays_iso_code='',
            )
        ]

        self.assertEqual(access_title_country(access_titles), '')

        # With several selected access titles
        access_titles = [
            TitreAccesSelectionnableDTO(
                type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name,
                selectionne=True,
                uuid_experience=uuid_experience,
                annee=2020,
                pays_iso_code='BE',
            ),
            TitreAccesSelectionnableDTO(
                type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name,
                selectionne=False,
                uuid_experience=uuid_experience,
                annee=2021,
                pays_iso_code='FR',
            ),
            TitreAccesSelectionnableDTO(
                type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name,
                selectionne=True,
                uuid_experience=uuid_experience,
                annee=2022,
                pays_iso_code='',
            ),
            TitreAccesSelectionnableDTO(
                type_titre=TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name,
                selectionne=True,
                uuid_experience=uuid_experience,
                annee=2015,
                pays_iso_code='UK',
            ),
        ]

        self.assertEqual(access_title_country(access_titles), 'BE')

        # With several selected access titles the same year
        access_titles = [
            TitreAccesSelectionnableDTO(
                type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name,
                selectionne=True,
                uuid_experience=uuid_experience,
                annee=2020,
                pays_iso_code='BE',
            ),
            TitreAccesSelectionnableDTO(
                type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name,
                selectionne=True,
                uuid_experience=uuid_experience,
                annee=2020,
                pays_iso_code='FR',
            ),
            TitreAccesSelectionnableDTO(
                type_titre=TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name,
                selectionne=True,
                uuid_experience=uuid_experience,
                annee=2022,
                pays_iso_code='',
            ),
        ]

        self.assertEqual(access_title_country(access_titles), 'BE')
