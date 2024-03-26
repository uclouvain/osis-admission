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
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, SicManagementRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory


@freezegun.freeze_time('2020-12-01')
class GeneralOtherAdmissionsListViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce(2020, number_past=1, number_future=1)
        cls.entity = EntityVersionFactory().entity
        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.entity).person.user
        cls.general_admission = GeneralEducationAdmissionFactory(
            training__academic_year=cls.academic_years[1],
            determined_academic_year=cls.academic_years[1],
            training__management_entity=cls.entity,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        cls.url = resolve_url('admission:general-education:other-admissions-list', uuid=cls.general_admission.uuid)

    def test_with_no_other_admission(self):
        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 0)

    def test_depending_on_admission_candidate(self):
        # Admission with the same candidate -> retrieve it
        other_admission = GeneralEducationAdmissionFactory(
            training__academic_year=self.general_admission.training.academic_year,
            determined_academic_year=self.general_admission.determined_academic_year,
            candidate=self.general_admission.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 1)

        # Admission with a different candidate -> don't retrieve it
        other_admission.candidate = CandidateFactory().person
        other_admission.save(update_fields=['candidate'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 0)

    def test_depending_on_admission_year(self):
        # Admission with the same determined academic year -> retrieve it
        other_admission = GeneralEducationAdmissionFactory(
            training__academic_year=self.general_admission.training.academic_year,
            determined_academic_year=self.general_admission.determined_academic_year,
            candidate=self.general_admission.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 1)

        # Admission with the same training academic year but no determined academic year -> retrieve it
        other_admission.determined_academic_year = None
        other_admission.save(update_fields=['determined_academic_year'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 1)

        # Admission with a different training academic year and no determined academic year -> don't retrieve it
        other_admission.training.academic_year = self.academic_years[0]
        other_admission.training.save(update_fields=['academic_year'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 0)

    def test_depending_on_admission_status(self):
        # Admission with the right candidate, year and status -> retrieve it
        other_admission = GeneralEducationAdmissionFactory(
            training__academic_year=self.general_admission.training.academic_year,
            determined_academic_year=self.general_admission.determined_academic_year,
            candidate=self.general_admission.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 1)

        # Invalid status -> don't retrieve it
        for status in [
            ChoixStatutPropositionGenerale.ANNULEE.name,
            ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
            ChoixStatutPropositionGenerale.EN_BROUILLON.name,
        ]:
            other_admission.status = status
            other_admission.save(update_fields=['status'])

            response = self.client.get(self.url)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                len(response.context['autres_demandes']),
                0,
                'No admission must be returned for status "{}"'.format(status),
            )

    def test_with_doctorate_admission(self):
        # Admission with the right candidate, year and status -> retrieve it
        other_admission = DoctorateAdmissionFactory(
            training__academic_year=self.general_admission.training.academic_year,
            determined_academic_year=self.general_admission.determined_academic_year,
            candidate=self.general_admission.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 1)

        # Admission with the wrong status -> don't retrieve it
        other_admission.status = ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name
        other_admission.save(update_fields=['status'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 0)

    def test_with_continuing_admission(self):
        # Admission with the right candidate, year and status -> retrieve it
        other_admission = ContinuingEducationAdmissionFactory(
            training__academic_year=self.general_admission.training.academic_year,
            determined_academic_year=self.general_admission.determined_academic_year,
            candidate=self.general_admission.candidate,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )

        self.client.force_login(self.sic_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['autres_demandes']), 1)
