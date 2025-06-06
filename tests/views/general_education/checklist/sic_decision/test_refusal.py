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
import datetime

import freezegun
from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_history.models import HistoryEntry

from admission.models import GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import ENTITY_CDE
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
    TypeDeRefus,
)
from admission.tests.factories.faculty_decision import RefusalReasonFactory
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from admission.tests.views.general_education.checklist.sic_decision.base import SicPatchMixin
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory


@freezegun.freeze_time('2021-11-01')
class SicRefusalDecisionViewTestCase(SicPatchMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = GeneralEducationTrainingFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=cls.training,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
        )
        cls.url = resolve_url(
            'admission:general-education:sic-decision-refusal',
            uuid=cls.general_admission.uuid,
        )

    def test_submit_refusal_decision_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_refusal_decision_form_initialization_no_reason(self):
        self.client.force_login(user=self.sic_manager_user)

        self.general_admission.refusal_reasons.all().delete()
        self.general_admission.other_refusal_reasons = []
        self.general_admission.refusal_type = ''

        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_refusal_form']

        self.assertEqual(form.initial.get('reasons'), [])
        self.assertEqual(form.initial.get('refusal_type'), '')

    def test_refusal_decision_form_initialization_one_reason(self):
        self.client.force_login(user=self.sic_manager_user)
        refusal_reason = RefusalReasonFactory()

        self.general_admission.refusal_reasons.add(refusal_reason)
        self.general_admission.refusal_type = TypeDeRefus.REFUS_AGREGATION.name
        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_refusal_form']

        self.assertEqual(form.initial.get('reasons'), [refusal_reason.uuid])
        self.assertEqual(form.initial.get('refusal_type'), TypeDeRefus.REFUS_AGREGATION.name)

    def test_refusal_decision_form_initialization_other_reason(self):
        self.client.force_login(user=self.sic_manager_user)
        refusal_reason = RefusalReasonFactory()

        self.general_admission.refusal_reasons.all().delete()
        self.general_admission.other_refusal_reasons = ['Other reason']
        self.general_admission.save()

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        form = response.context['sic_decision_refusal_form']

        self.assertEqual(form.initial.get('reasons'), ['Other reason'])

    def test_refusal_decision_form_submitting_with_invalid_data(self):
        self.client.force_login(user=self.sic_manager_user)

        # Check form submitting
        self.general_admission.refusal_reasons.all().delete()
        self.general_admission.other_refusal_reasons = []
        self.general_admission.save()

        # No chosen reason
        response = self.client.post(
            self.url,
            data={'sic-decision-refusal-refusal_type': ''},
            **self.default_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.headers.get('HX-Refresh'), True)

        form = response.context['sic_decision_refusal_form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('refusal_type', []))

    def test_refusal_decision_form_submitting_with_valid_data_existing_reason(self):
        self.client.force_login(user=self.sic_manager_user)
        refusal_reason = RefusalReasonFactory()

        data = {
            'sic-decision-refusal-refusal_type': 'REFUS_DOSSIER_TARDIF',
            'sic-decision-refusal-reasons': [refusal_reason.uuid],
        }

        # Choose an existing reason
        response = self.client.post(self.url, data=data, **self.default_headers)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get('HX-Refresh'))

        form = response.context['sic_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        refusal_reasons = self.general_admission.refusal_reasons.all()
        self.assertEqual(len(refusal_reasons), 1)
        self.assertEqual(refusal_reasons[0], refusal_reason)
        self.assertEqual(self.general_admission.other_refusal_reasons, [])
        self.assertEqual(self.general_admission.refusal_type, 'REFUS_DOSSIER_TARDIF')
        self.assertEqual(
            self.general_admission.status, ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['extra'],
            {'en_cours': 'refusal'},
        )
        self.assertEqual(self.general_admission.last_update_author, self.sic_manager_user.person)
        self.assertEqual(self.general_admission.modified_at, datetime.datetime.now())

        # Check that an history entry is created
        entries: QuerySet[HistoryEntry] = HistoryEntry.objects.filter(
            object_uuid=self.general_admission.uuid,
        )

        self.assertEqual(len(entries), 1)

        self.assertCountEqual(
            ['proposition', 'sic-decision', 'status-changed', 'specify-refusal-reasons'],
            entries[0].tags,
        )

        self.assertEqual(
            entries[0].author,
            f'{self.sic_manager_user.person.first_name} {self.sic_manager_user.person.last_name}',
        )

        # Check that no additional history entry is created
        response = self.client.post(self.url, data=data, **self.default_headers)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(HistoryEntry.objects.filter(object_uuid=self.general_admission.uuid).count(), 1)

    def test_refusal_decision_form_submitting_with_valid_data_other_reason(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.post(
            self.url,
            data={
                'sic-decision-refusal-refusal_type': 'REFUS_DOSSIER_TARDIF',
                'sic-decision-refusal-reasons': ['My other reason'],
            },
            **self.default_headers,
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get('HX-Refresh'))

        form = response.context['sic_decision_refusal_form']
        self.assertTrue(form.is_valid())

        # Check that the admission has been updated
        self.general_admission.refresh_from_db()

        self.assertEqual(self.general_admission.refusal_type, 'REFUS_DOSSIER_TARDIF')
        self.assertFalse(self.general_admission.refusal_reasons.exists())
        self.assertEqual(self.general_admission.other_refusal_reasons, ['My other reason'])
        self.assertEqual(
            self.general_admission.status, ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['statut'],
            ChoixStatutChecklist.GEST_EN_COURS.name,
        )
        self.assertEqual(
            self.general_admission.checklist['current']['decision_sic']['extra'],
            {'en_cours': 'refusal'},
        )
