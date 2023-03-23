# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from email import message_from_string

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from admission.contrib.models import CddMailTemplate
from admission.mail_templates import ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CddManagerFactory
from admission.tests.factories.supervision import CaMemberFactory, ExternalPromoterFactory, PromoterFactory
from base.tests.factories.entity import EntityFactory
from osis_notification.models import EmailNotification


class SendMailDoctorateStudentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cdd = doctoral_commission = EntityFactory()
        process = PromoterFactory().process
        CaMemberFactory(process=process)
        ExternalPromoterFactory(process=process)
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=doctoral_commission,
            admitted=True,
            candidate__language=settings.LANGUAGE_CODE_EN,
            supervision_group=process,
        )
        cls.user = CddManagerFactory(entity=doctoral_commission).person.user
        cls.url = resolve_url('admission:doctorate:send-mail', uuid=cls.admission.uuid)

    def test_prefill_no_selection(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.context['form'].initial.get('subject', ''), '')

    def test_prefill_select_generic(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?template=' + ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.context['form'].initial.get('subject', ''), '')

    def test_prefill_selecting_custom(self):
        self.client.force_login(self.user)

        tpl = CddMailTemplate.objects.create(
            identifier=ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED,
            name="Some name",
            language=settings.LANGUAGE_CODE_EN,
            cdd=self.cdd,
            subject="Subject",
            body="Body",
        )
        response = self.client.get(self.url + '?template=' + str(tpl.pk))
        self.assertEqual(response.context['form'].initial.get('body', ''), 'Body')

    def test_send_mail_doctorate_post_with_cc(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                'subject': 'Hello',
                'body': 'World',
                'cc_promoteurs': True,
                'cc_membres_ca': True,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, self.url)
        self.assertEqual(EmailNotification.objects.count(), 1)
        email_message = message_from_string(EmailNotification.objects.first().payload)
        self.assertEqual(len(email_message['Cc'].split(',')), 3)

    def test_send_mail_doctorate_post_without_cc(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                'subject': 'Hello',
                'body': 'World',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, self.url)
        self.assertEqual(EmailNotification.objects.count(), 1)
        email_message = message_from_string(EmailNotification.objects.first().payload)
        self.assertNotIn('Cc', email_message)
