# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime

from django.test import TestCase

from admission.infrastructure.admission.domain.service.titres_acces import TitresAcces
from admission.tests.factories.curriculum import ProfessionalExperienceFactory
from base.tests.factories.person import PersonFactory
from osis_profile.models.enums.curriculum import ActivitySector, ActivityType


class TitresAccesTestCase(TestCase):
    def test_pas_de_diplome(self):
        person = PersonFactory()
        result = TitresAcces.conditions_remplies(person.global_id, [])
        self.assertFalse(result.diplomation_secondaire_belge)
        self.assertFalse(result.diplomation_secondaire_etranger)
        self.assertFalse(result.alternative_etudes_secondaires)
        self.assertFalse(result.potentiel_bachelier_belge_sans_diplomation)
        self.assertFalse(result.diplomation_academique_belge)
        self.assertFalse(result.diplomation_academique_etranger)
        self.assertFalse(result.potentiel_master_belge_sans_diplomation)
        self.assertFalse(result.diplomation_potentiel_master_belge)
        self.assertFalse(result.diplomation_potentiel_master_etranger)
        self.assertFalse(result.diplomation_potentiel_doctorat_belge)
        self.assertFalse(result.potentiel_acces_vae)

    def test_vae(self):
        person = PersonFactory()
        # 18 mois
        ProfessionalExperienceFactory(
            person=person,
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 7, 1),
            type=ActivityType.WORK.name,
            role='Librarian',
            sector=ActivitySector.PUBLIC.name,
            activity='Work - activity',
        )
        # 2 ans
        ProfessionalExperienceFactory(
            person=person,
            start_date=datetime.date(2018, 1, 1),
            end_date=datetime.date(2020, 1, 1),
            type=ActivityType.WORK.name,
            role='Mechanician',
            sector=ActivitySector.PRIVATE.name,
            activity='Work - activity',
        )

        result = TitresAcces.conditions_remplies(person.global_id, [])
        self.assertTrue(result.potentiel_acces_vae)
