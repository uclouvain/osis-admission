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
import datetime
import io
from tempfile import NamedTemporaryFile

import freezegun
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook, load_workbook

from admission.auth.scope import Scope
from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.models.contingente import ContingenteTraining
from admission.tests.factories.contingente import ContingenteTrainingFactory
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.roles import CentralManagerRoleFactory
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_calendar import AcademicCalendarFactory


@freezegun.freeze_time('2026-01-01')
@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class ContingenteManageViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CentralManagerRoleFactory(scopes=[Scope.CONTINGENTE_NON_RESIDENT.name]).person.user

        cls.first_training = GeneralEducationTrainingFactory(
            academic_year__year=2026,
            acronym=SIGLES_WITH_QUOTA[0],
        )
        cls.second_training = GeneralEducationTrainingFactory(
            academic_year__year=2026,
            acronym=SIGLES_WITH_QUOTA[1],
        )
        AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=datetime.date(2025, 9, 15),
            end_date=datetime.date(2026, 9, 15),
            data_year=cls.first_training.academic_year,
        )
        cls.contingente_training = ContingenteTrainingFactory(training=cls.second_training)
        cls.admission = GeneralEducationAdmissionFactory(
            candidate__birth_date=datetime.date(2000, 1, 1),
            training=cls.second_training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            is_non_resident=True,
            ares_application_number='ARES_NUMBER',
        )

    def test_contingente_manage_view_get(self):
        self.client.force_login(user=self.user)

        response = self.client.get(reverse('admission:contingente:index'))

        self.assertTemplateUsed(response, 'admission/general_education/contingente/manage.html')

    def test_contingente_training_manage_view_get(self):
        self.client.force_login(user=self.user)

        response = self.client.get(reverse('admission:contingente:training') + f'?training={SIGLES_WITH_QUOTA[0]}')

        self.assertTemplateUsed(response, 'admission/general_education/contingente/manage_training.html')
        self.assertTrue(ContingenteTraining.objects.filter(training=self.first_training).exists())

    def test_contingente_training_manage_view_get_unknown_training(self):
        self.client.force_login(user=self.user)

        response = self.client.get(reverse('admission:contingente:training') + f'?training=OIHGEHGQ')

        self.assertEqual(response.status_code, 404)

    def test_contingente_training_update_view_get(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            reverse('admission:contingente:training_change', kwargs={'training': SIGLES_WITH_QUOTA[1]})
        )

        self.assertRedirects(response, reverse('admission:contingente:index'))

    def test_contingente_training_update_view_post(self):
        self.client.force_login(user=self.user)

        response = self.client.post(
            reverse('admission:contingente:training_change', kwargs={'training': SIGLES_WITH_QUOTA[1]}),
            data={'places_number': 42},
            headers={'HX-Request': "true"},
        )

        self.assertTemplateUsed(response, 'admission/general_education/contingente/contingente_training_form.html')
        self.contingente_training.refresh_from_db()
        self.assertEqual(self.contingente_training.places_number, 42)

    def test_contingente_training_export_view_get(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            reverse('admission:contingente:training_export', kwargs={'training': SIGLES_WITH_QUOTA[1]}),
        )

        self.assertEqual(response.headers['content-type'], 'application/vnd.ms-excel')
        wb = load_workbook(io.BytesIO(b"".join(response.streaming_content)))
        ws = wb.active
        lines = [[cell.value for cell in line] for line in ws]
        self.assertEqual(lines[1][10], self.admission.ares_application_number)

    def test_contingente_training_import_view_post(self):
        self.client.force_login(user=self.user)

        headers = [
            "NOM",
            "PREMIER PRENOM",
            "AUTRE PRENOM",
            "SEXE",
            "LIEU DE NAISSANCE",
            "DATE DE NAISSANCE",
            "NATIONALITE",
            "NUMERO DE LA PIECE D'IDENTITE",
            "INSTITUTION D'ENSEIGNEMENT(HAUTE ECOLE ou UNIVERSITE)",
            "GRADE CHOISI",
            "N° DOSSIER",
            "N° HUISSIER",
            "SCEAU HUISSIER",
        ]
        line = [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "VETE",
            self.admission.ares_application_number,
            "1",
            "",
        ]
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        ws.append(line)
        excel_file = NamedTemporaryFile()
        wb.save(excel_file.name)
        excel_file.seek(0)
        excel_file.name = 'file.xlsx'

        response = self.client.post(
            reverse('admission:contingente:training_import', kwargs={'training': SIGLES_WITH_QUOTA[1]}),
            data={'import_file': excel_file},
            headers={'HX-Request': "true"},
        )
        self.assertTemplateUsed(response, "admission/general_education/contingente/manage_training_import.html")
        self.admission.refresh_from_db()
        self.contingente_training.refresh_from_db()
        self.assertEqual(self.contingente_training.last_import_at, datetime.datetime.now())
        self.assertEqual(self.contingente_training.last_import_by, self.user.person)
        self.assertEqual(self.admission.draw_number, 1)
