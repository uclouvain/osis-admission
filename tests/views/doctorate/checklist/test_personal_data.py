# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    OngletsChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
)
from admission.models import DoctorateAdmission
from admission.tests.factories.doctorate import (
    DoctorateAdmissionFactory,
    DoctorateFactory,
)
from admission.tests.factories.roles import (
    CentralManagerRoleFactory,
    ProgramManagerRoleFactory,
)
from base.tests.factories.entity import EntityWithVersionFactory


class PersonalDataChangeStatusViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.entity = EntityWithVersionFactory()

        cls.training = DoctorateFactory(management_entity=cls.entity)
        cls.program_manager = ProgramManagerRoleFactory(education_group=cls.training.education_group).person
        cls.central_manager = CentralManagerRoleFactory(entity=cls.entity).person
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.base_url = 'admission:doctorate:personal-data-change-status'
        cls.checklist_statuses = ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.donnees_personnelles.name]

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

    def test_change_the_checklist_status_is_forbidden_with_program_manager_user(self):
        self.client.force_login(user=self.program_manager.user)

        url = resolve_url(self.base_url, uuid=self.admission.uuid, status=ChoixStatutChecklist.INITIAL_CANDIDAT.name)

        response = self.client.post(url, **self.default_headers)
        self.assertEqual(response.status_code, 403)

    def test_change_the_checklist_status_with_central_manager_user(self):
        self.client.force_login(user=self.central_manager.user)

        # To be processed
        status = self.checklist_statuses['A_TRAITER']
        url = resolve_url(self.base_url, uuid=self.admission.uuid, status=status.statut.name)

        response = self.client.post(
            url,
            data=status.extra,
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.admission.refresh_from_db()

        self.assertEqual(
            self.admission.checklist['current'][OngletsChecklist.donnees_personnelles.name]['statut'],
            ChoixStatutChecklist.INITIAL_CANDIDAT.name,
        )
        self.assertEqual(self.admission.checklist['current'][OngletsChecklist.donnees_personnelles.name]['extra'], {})

        # To be completed
        status = self.checklist_statuses['A_COMPLETER']
        url = resolve_url(self.base_url, uuid=self.admission.uuid, status=status.statut.name)

        response = self.client.post(
            url,
            data=status.extra,
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.admission.refresh_from_db()

        self.assertEqual(
            self.admission.checklist['current'][OngletsChecklist.donnees_personnelles.name]['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.admission.checklist['current'][OngletsChecklist.donnees_personnelles.name]['extra'],
            {'fraud': '0'},
        )

        # Fraudster
        status = self.checklist_statuses['FRAUDEUR']
        url = resolve_url(self.base_url, uuid=self.admission.uuid, status=status.statut.name)

        response = self.client.post(
            url,
            data=status.extra,
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.admission.refresh_from_db()

        self.assertEqual(
            self.admission.checklist['current'][OngletsChecklist.donnees_personnelles.name]['statut'],
            ChoixStatutChecklist.GEST_BLOCAGE.name,
        )
        self.assertEqual(
            self.admission.checklist['current'][OngletsChecklist.donnees_personnelles.name]['extra'],
            {'fraud': '1'},
        )

        # Validated
        status = self.checklist_statuses['VALIDEES']
        url = resolve_url(self.base_url, uuid=self.admission.uuid, status=status.statut.name)

        response = self.client.post(
            url,
            data=status.extra,
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.admission.refresh_from_db()

        self.assertEqual(
            self.admission.checklist['current'][OngletsChecklist.donnees_personnelles.name]['statut'],
            ChoixStatutChecklist.GEST_REUSSITE.name,
        )
        self.assertEqual(self.admission.checklist['current'][OngletsChecklist.donnees_personnelles.name]['extra'], {})
