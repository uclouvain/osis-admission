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
from unittest import mock

from django.shortcuts import resolve_url
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.formation_generale.events import DonneesPersonellesCandidatValidee
from admission.models import DoctorateAdmission
from admission.tests.factories.doctorate import (
    DoctorateAdmissionFactory,
    DoctorateFactory,
)
from admission.tests.factories.roles import (
    CentralManagerRoleFactory,
    ProgramManagerRoleFactory,
)
from base.models.enums.personal_data import ChoixStatutValidationDonneesPersonnelles
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

    def setUp(self) -> None:
        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=self.training,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        self.url = resolve_url(self.base_url, uuid=self.admission.uuid)

        publish_mock = mock.patch('infrastructure.utils.MessageBus.publish')
        self.publish_mock = publish_mock.start()
        self.addCleanup(publish_mock.stop)

    def test_change_the_checklist_status_with_program_manager_user(self):
        self.client.force_login(user=self.program_manager.user)

        status = ChoixStatutValidationDonneesPersonnelles.A_TRAITER.name
        response = self.client.post(
            self.url,
            data={'status': status},
            **self.default_headers,
        )
        self.assertEqual(response.status_code, 403)

        self.admission.status = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name
        self.admission.save()

        # Authorized statuses
        authorized_statuses = [
            ChoixStatutValidationDonneesPersonnelles.TOILETTEES.name,
            ChoixStatutValidationDonneesPersonnelles.A_TRAITER.name,
        ]

        for status in authorized_statuses:
            response = self.client.post(
                self.url,
                data={'status': status},
                **self.default_headers,
            )

            self.assertEqual(response.status_code, 200)

            self.admission.candidate.refresh_from_db()

            self.assertEqual(self.admission.candidate.personal_data_validation_status, status)

        # Unauthorized statuses
        for status in ChoixStatutValidationDonneesPersonnelles.get_names_except(*authorized_statuses):
            response = self.client.post(
                self.url,
                data={'status': status},
                **self.default_headers,
            )

            self.assertEqual(response.status_code, 403)

    def test_change_the_checklist_status_with_central_manager_user(self):
        self.client.force_login(user=self.central_manager.user)

        for status in ChoixStatutValidationDonneesPersonnelles.get_names():
            self.publish_mock.reset_mock()

            response = self.client.post(
                self.url,
                data={'status': status},
                **self.default_headers,
            )

            self.assertEqual(response.status_code, 200)

            self.admission.candidate.refresh_from_db()

            self.assertEqual(self.admission.candidate.personal_data_validation_status, status)

            if status == ChoixStatutValidationDonneesPersonnelles.VALIDEES.name:
                self.publish_mock.assert_called_once_with(
                    DonneesPersonellesCandidatValidee(
                        matricule=self.admission.candidate.global_id,
                        transaction_id=mock.ANY,
                        entity_id=None,
                    )
                )
            else:
                self.publish_mock.assert_not_called()
