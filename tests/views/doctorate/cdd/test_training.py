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
from unittest.mock import patch

import freezegun
from django.conf import settings
from django.forms import Field
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _, pgettext
from rest_framework import status

from admission.contrib.models.cdd_config import CddConfiguration
from admission.contrib.models.doctoral_training import Activity
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixTypeAdmission
from admission.ddd.parcours_doctoral.formation.domain.model.enums import (
    CategorieActivite,
    ChoixComiteSelection,
    ContexteFormation,
    StatutActivite,
)
from admission.forms.doctorate.training.activity import INSTITUTION_UCL
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.activity import *
from admission.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from osis_notification.models import WebNotification


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateTrainingActivityViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # A doctorate without doctoral and complementary training
        cls.restricted_doctorate = DoctorateAdmissionFactory(type=ChoixTypeAdmission.PRE_ADMISSION.name, admitted=True)
        CddConfiguration.objects.create(cdd=cls.restricted_doctorate.training.management_entity)

        # A normal doctorate
        cls.reference_promoter = PromoterFactory(is_reference_promoter=True)
        cls.conference = ConferenceFactory(
            ects=10,
            doctorate__supervision_group=cls.reference_promoter.process,
        )
        cls.namespace = 'admission:doctorate:doctoral-training'
        cls.doctorate = cls.conference.doctorate
        cls.service = ServiceFactory(doctorate=cls.doctorate)
        cls.ucl_course = UclCourseFactory(doctorate=cls.doctorate, learning_unit_year__academic_year__current=True)

        # A manager that can manage both doctorates
        manager_person = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        cls.manager = manager_person.user
        CddConfiguration.objects.create(
            cdd=cls.doctorate.training.management_entity,
            is_complementary_training_enabled=True,
        )
        ProgramManagerFactory(education_group=cls.restricted_doctorate.training.education_group, person=manager_person)

        cls.url = resolve_url(cls.namespace, uuid=cls.doctorate.uuid)
        cls.default_url_args = dict(uuid=cls.doctorate.uuid, activity_id=cls.conference.uuid)

    def setUp(self) -> None:
        self.client.force_login(self.manager)

    def test_view(self):
        response = self.client.get(self.url)
        self.assertContains(response, self.conference.title)
        self.assertContains(response, _("NON_SOUMISE"))
        self.assertEqual(repr(self.conference), "Colloques et conférences (10 ects, Non soumise)")
        self.assertEqual(
            str(self.conference),
            f"Conférence nationale : {self.conference.title}"
            f" ({self.conference.city}, {self.conference.country}) - 10 ECTS",
        )

        # With an unsubmitted conference and unsubmitted service, we should have these links
        url = resolve_url(f'{self.namespace}:add', uuid=self.doctorate.uuid, category='communication')
        self.assertContains(response, f"{url}?parent={self.conference.uuid}")
        url = resolve_url(f'{self.namespace}:add', uuid=self.doctorate.uuid, category='publication')
        self.assertContains(response, f"{url}?parent={self.conference.uuid}")
        self.assertContains(response, resolve_url(f'{self.namespace}:edit', **self.default_url_args))
        self.assertContains(response, resolve_url(f'{self.namespace}:delete', **self.default_url_args))

    def test_boolean_select_is_online(self):
        add_url = resolve_url(f'{self.namespace}:add', uuid=self.doctorate.uuid, category='communication')
        response = self.client.get(add_url)
        default_input = (
            '<input type="radio" name="is_online" value="False" class="" title="" id="id_is_online_0" checked>'
        )
        self.assertContains(response, default_input, html=True)

    @freezegun.freeze_time('2022-11-01')
    def test_academic_year_field(self):
        AcademicYearFactory(year=2022)
        add_url = resolve_url(f'{self.namespace}:add', uuid=self.doctorate.uuid, category='course')
        response = self.client.get(add_url)
        self.assertContains(response, "2022-2023", html=True)

    def test_boolean_select_is_online_with_value(self):
        add_url = resolve_url(f'{self.namespace}:add', uuid=self.doctorate.uuid, category='communication')
        response = self.client.post(add_url, {'is_online': True})
        default_input = (
            '<input type="radio" name="is_online" value="False" class="" title="" id="id_is_online_0" checked>'
        )
        self.assertNotContains(response, default_input, html=True)

    def test_form(self):
        add_url = resolve_url(f'{self.namespace}:add', uuid=self.doctorate.uuid, category='service')
        with translation.override(settings.LANGUAGE_CODE_FR):
            response = self.client.get(add_url)
            self.assertContains(response, "Coopération internationale")

        # Field is other
        response = self.client.post(add_url, {'type': "Foobar"}, follow=True)
        just_created = Activity.objects.first()
        self.assertIn(self.url, response.redirect_chain[-1][0])
        self.assertIn(str(just_created.uuid), response.redirect_chain[-1][0])
        self.assertEqual(just_created.type, "Foobar")

        # Field is one of provided values
        response = self.client.post(add_url, {'type': "Coopération internationale"}, follow=True)
        self.assertEqual(Activity.objects.first().type, "Coopération internationale")
        self.assertIn(self.url, response.redirect_chain[-1][0])

        # Start date must be before end date
        data = {
            'type': "Coopération internationale",
            'start_date': '02/01/2022',
            'end_date': '01/01/2022',
        }
        response = self.client.post(add_url, data)
        self.assertFormError(response, 'form', 'start_date', _("The start date can't be later than the end date"))

    def test_training_restricted(self):
        url = resolve_url(f'admission:doctorate:doctoral-training', uuid=self.restricted_doctorate.uuid)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        url = resolve_url(f'admission:doctorate:complementary-training', uuid=self.restricted_doctorate.uuid)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        url = resolve_url(f'admission:doctorate:course-enrollment', uuid=self.restricted_doctorate.uuid)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = resolve_url(
            f'admission:doctorate:course-enrollment:add',
            uuid=self.restricted_doctorate.uuid,
            category="ucl_course",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.context['form'].fields['context'].widget.choices), 1)

    @freezegun.freeze_time('2022-11-01')
    def test_complementary_training_course(self):
        url = resolve_url(
            f'admission:doctorate:course-enrollment:edit',
            uuid=self.doctorate.uuid,
            activity_id=self.ucl_course.uuid,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = {
            'context': ContexteFormation.COMPLEMENTARY_TRAINING.name,
            'academic_year': self.ucl_course.learning_unit_year.academic_year.year,
            'learning_unit_year': self.ucl_course.learning_unit_year.acronym,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_ucl_course(self):
        url = resolve_url(
            f'admission:doctorate:complementary-training:add',
            uuid=self.doctorate.uuid,
            category='COURSE',
        )
        response = self.client.post(url, {'type': "Foobar", "organizing_institution": INSTITUTION_UCL})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        just_created = Activity.objects.first()
        self.assertEqual(just_created.context, ContexteFormation.COMPLEMENTARY_TRAINING.name)

    def test_missing_form(self):
        add_url = resolve_url(f'{self.namespace}:add', uuid=self.doctorate.uuid, category='foobar')
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_parent(self):
        add_url = resolve_url(f'{self.namespace}:add', uuid=self.doctorate.uuid, category='publication')

        # test inexistent parent
        response = self.client.get(f"{add_url}?parent={uuid.uuid4()}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # test inexistent form combination
        response = self.client.get(f"{add_url}?parent={self.service.uuid}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # test normal behavior
        response = self.client.get(f"{add_url}?parent={self.conference.uuid}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(f"{add_url}?parent={self.conference.uuid}", {}, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_edit(self):
        # Test edit
        edit_url = resolve_url(
            f'{self.namespace}:edit',
            uuid=self.doctorate.uuid,
            activity_id=self.service.uuid,
        )
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(edit_url, {'type': "Foobar"})
        self.assertRedirects(response, f"{self.url}#{self.service.uuid}")
        self.service.refresh_from_db()
        self.assertEqual(self.service.type, "Foobar")
        response = self.client.get(edit_url)
        self.assertContains(response, "Foobar")

        # Test edit a child activity
        child = PublicationFactory(doctorate=self.doctorate, parent=self.conference)
        edit_url = resolve_url(f'{self.namespace}:edit', uuid=self.doctorate.uuid, activity_id=child.uuid)
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('osis_document.api.utils.get_remote_token')
    @patch('osis_document.api.utils.get_remote_metadata')
    @patch('osis_document.api.utils.get_several_remote_metadata')
    @patch('osis_document.api.utils.confirm_remote_upload')
    @patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
    def test_remove_proof_if_not_needed(
        self,
        file_confirm_upload,
        confirm_remote_upload,
        get_several_remote_metadata,
        get_remote_metadata,
        get_remote_token,
    ):
        get_several_remote_metadata.side_effect = lambda tokens: {token: {"name": "test.pdf"} for token in tokens}
        get_remote_metadata.return_value = {"name": "test.pdf"}
        get_remote_token.return_value = "test"
        confirm_remote_upload.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'
        file_confirm_upload.side_effect = lambda _, att_values, __: [
            "4bdffb42-552d-415d-9e4c-725f10dce228" for _ in att_values
        ]

        # Communication
        activity = ActivityFactory(
            doctorate=self.doctorate,
            category=CategorieActivite.COMMUNICATION.name,
        )
        edit_url = resolve_url(f'{self.namespace}:edit', uuid=self.doctorate.uuid, activity_id=activity.uuid)
        response = self.client.post(
            edit_url,
            {
                'type': 'Some type',
                'subtype': 'Some type',
                'committee': ChoixComiteSelection.NO.name,
                'acceptation_proof_0': 'test',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        activity.refresh_from_db()
        self.assertEqual(activity.acceptation_proof, [])
        response = self.client.post(
            edit_url,
            {
                'type': 'Some type',
                'subtype': 'Some type',
                'committee': ChoixComiteSelection.YES.name,
                'acceptation_proof_0': 'test',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        activity.refresh_from_db()
        self.assertEqual(activity.acceptation_proof, [uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')])

        # Conference communication
        child = ActivityFactory(
            doctorate=self.doctorate,
            category=CategorieActivite.COMMUNICATION.name,
            parent=self.conference,
        )
        edit_url = resolve_url(f'{self.namespace}:edit', uuid=self.doctorate.uuid, activity_id=child.uuid)
        response = self.client.post(
            edit_url,
            {
                'type': 'Some type',
                'committee': ChoixComiteSelection.NO.name,
                'acceptation_proof_0': 'test',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        child.refresh_from_db()
        self.assertEqual(child.acceptation_proof, [])
        response = self.client.post(
            edit_url,
            {
                'type': 'Some type',
                'committee': ChoixComiteSelection.YES.name,
                'acceptation_proof_0': 'test',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        child.refresh_from_db()
        self.assertEqual(child.acceptation_proof, [uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')])

    def test_submit_activities(self):
        response = self.client.post(self.url, {'activity_ids': [self.service.uuid]}, follow=True)
        self.assertContains(response, _('SOUMISE'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_accept_activities(self):
        communication = CommunicationFactory(doctorate=self.doctorate, status=StatutActivite.SOUMISE.name)
        response = self.client.post(self.url, {'activity_ids': [communication.uuid], '_accept': True}, follow=True)
        self.assertContains(response, pgettext('publication-status', 'Accepted'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(WebNotification.objects.count(), 1)

    def test_delete_activity(self):
        child = PublicationFactory(doctorate=self.doctorate, parent=self.conference)
        url = resolve_url(f'{self.namespace}:delete', **self.default_url_args)
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(Activity.objects.filter(pk__in=[child.pk, self.conference.pk]).first())

    @freezegun.freeze_time('2022-11-01')
    def test_course_dates(self):
        activity = CourseFactory(doctorate=self.doctorate)
        edit_url = resolve_url(f'{self.namespace}:edit', uuid=self.doctorate.uuid, activity_id=activity.uuid)
        year = AcademicYearFactory(year=2022)
        response = self.client.post(
            edit_url,
            {
                'type': 'Some type',
                'organizing_institution': "Lorem",
                'academic_year': year.pk,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        activity.refresh_from_db()
        self.assertIsNone(activity.start_date)

        response = self.client.post(
            edit_url,
            {
                'type': 'Some type',
                'organizing_institution': INSTITUTION_UCL,
                'academic_year': year.pk,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        activity.refresh_from_db()
        self.assertEqual(activity.start_date.year, 2022)

        response = self.client.get(edit_url)
        self.assertContains(response, f'<option value="{year.pk}" selected>2022-2023</option>')

    def test_submit_without_activities(self):
        response = self.client.post(self.url, {'activity_ids': []})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', None, _("Select at least one activity"))

    @patch('osis_document.api.utils.get_remote_token')
    @patch('osis_document.api.utils.get_several_remote_metadata')
    @patch('osis_document.api.utils.confirm_remote_upload')
    @patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
    def test_submit_parent_seminar(
        self,
        file_confirm_upload,
        confirm_remote_upload,
        get_remote_metadata,
        get_remote_token,
    ):
        get_remote_metadata.side_effect = lambda tokens: {token: {"name": "test.pdf"} for token in tokens}
        get_remote_token.return_value = "test"
        confirm_remote_upload.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'
        file_confirm_upload.side_effect = lambda _, att_values, __: [
            "4bdffb42-552d-415d-9e4c-725f10dce228" for _ in att_values
        ]

        activity = SeminarCommunicationFactory(doctorate=self.doctorate)
        self.assertEqual(Activity.objects.filter(status='SOUMISE').count(), 0)
        response = self.client.post(self.url, {'activity_ids': [activity.parent.uuid]}, follow=True)
        self.assertContains(response, _('SOUMISE'))
        self.assertEqual(Activity.objects.filter(status='SOUMISE').count(), 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('osis_document.api.utils.get_remote_token')
    @patch('osis_document.api.utils.get_several_remote_metadata')
    @patch('osis_document.api.utils.confirm_remote_upload')
    @patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
    def test_submit_activities_with_error(
        self,
        file_confirm_upload,
        confirm_remote_upload,
        get_remote_metadata,
        get_remote_token,
    ):
        get_remote_metadata.side_effect = lambda tokens: {token: {"name": "test.pdf"} for token in tokens}
        get_remote_token.return_value = "test"
        confirm_remote_upload.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'
        file_confirm_upload.side_effect = lambda _, att_values, __: [
            "4bdffb42-552d-415d-9e4c-725f10dce228" for _ in att_values
        ]

        self.service.title = ""
        self.service.save()
        response = self.client.post(self.url, {'activity_ids': [self.service.uuid]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _('NON_SOUMISE'))
        self.assertFormError(response, 'form', None, _("This activity is not complete"))

        self.conference.title = ""
        self.conference.save()

        activity_list = [
            self.conference,
            SeminarFactory(doctorate=self.doctorate, title=""),
            ResidencyFactory(doctorate=self.doctorate),
            ConferenceCommunicationFactory(doctorate=self.doctorate),
            ConferencePublicationFactory(doctorate=self.doctorate),
            SeminarCommunicationFactory(doctorate=self.doctorate, title=""),
            ResidencyCommunicationFactory(doctorate=self.doctorate),
            CommunicationFactory(doctorate=self.doctorate),
            PublicationFactory(doctorate=self.doctorate),
            VaeFactory(doctorate=self.doctorate),
            CourseFactory(doctorate=self.doctorate),
            PaperFactory(doctorate=self.doctorate),
        ]
        response = self.client.post(self.url, {'activity_ids': [activity.uuid for activity in activity_list]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', None, _("This activity is not complete"))
        self.assertEqual(len(response.context['form'].activities_in_error), len(activity_list))

    def test_refuse_activity(self):
        self.conference.status = StatutActivite.SOUMISE.name
        self.conference.save()
        url = resolve_url(f'{self.namespace}:refuse', **self.default_url_args)
        response = self.client.get(url)
        self.assertContains(response, _("Refuse activity"))

        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "form", "reason", Field.default_error_messages['required'])

        response = self.client.post(url, {"reason": "Not ok"}, follow=True)
        self.assertRedirects(response, f"{self.url}#{self.conference.uuid}")

    def test_restore_activity(self):
        self.conference.status = StatutActivite.ACCEPTEE.name
        self.conference.save()
        url = resolve_url(f'{self.namespace}:restore', **self.default_url_args)
        response = self.client.get(url)
        self.assertContains(response, _("This activity will be restored"))

        response = self.client.post(url, {}, follow=True)
        self.assertRedirects(response, f"{self.url}#{self.conference.uuid}")
        self.conference.refresh_from_db()
        self.assertEqual(self.conference.status, StatutActivite.SOUMISE.name)
