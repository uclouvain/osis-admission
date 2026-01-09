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

from django.test import TestCase

from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
)
from admission.migrations.utils.initialize_iufc_admissions_personal_data_checklist import (
    initialize_iufc_admissions_personal_data_checklist,
)
from admission.models.base import BaseAdmission
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory


class InitializeIUFCAdmissionsPersonalDataChecklistTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.initial_personal_data_checklist = {
            'libelle': 'To be processed',
            'enfants': [],
            'extra': {},
            'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        }

    def test_do_not_update_if_the_personal_data_checklist_is_already_set(self):
        admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.CONFIRMEE.name)

        admission.checklist['current']['donnees_personnelles']['statut'] = ChoixStatutChecklist.GEST_EN_COURS.name
        admission.save(update_fields=['checklist'])

        initialize_iufc_admissions_personal_data_checklist(model_class=BaseAdmission)

        admission.refresh_from_db()

        self.assertEqual(
            admission.checklist['current']['donnees_personnelles']['statut'], ChoixStatutChecklist.GEST_EN_COURS.name
        )

    def test_do_not_update_if_the_checklist_is_not_already_set(self):
        admission = ContinuingEducationAdmissionFactory(status=ChoixStatutPropositionContinue.EN_BROUILLON.name)

        initialize_iufc_admissions_personal_data_checklist(model_class=BaseAdmission)

        admission.refresh_from_db()

        self.assertEqual(admission.checklist, {})

    def test_update(self):
        admission = ContinuingEducationAdmissionFactory(
            checklist={
                'initial': {},
                'current': {},
            }
        )

        initialize_iufc_admissions_personal_data_checklist(model_class=BaseAdmission)

        admission.refresh_from_db()

        self.assertEqual(admission.checklist['initial']['donnees_personnelles'], self.initial_personal_data_checklist)
        self.assertEqual(admission.checklist['current']['donnees_personnelles'], self.initial_personal_data_checklist)
