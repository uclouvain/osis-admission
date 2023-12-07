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

from django.db import migrations
from django.db.models import QuerySet
from osis_notification.models.enums import NotificationStates, NotificationTypes

from base.models.person import Person


def fix_notifications(apps, schema_editor):
    Notification = apps.get_model('osis_notification', 'Notification')
    notifications: QuerySet[Notification] = Notification.objects.select_related('person').filter(
        person__baseadmission__isnull=False,
        state=NotificationStates.PENDING_STATE.name,
        type=NotificationTypes.EMAIL_TYPE.name,
    )

    for notification in notifications:
        email_message = message_from_string(notification.payload)

        if notification.person and 'To' in email_message:

            if email_message['To'] == Person.get_str(notification.person.first_name, notification.person.last_name):
                email_message.replace_header('To', notification.person.email)
                notification.payload = str(email_message)
                notification.save(update_fields=['payload'])


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0132_checklist_financability'),
        ('osis_notification', '0002_person_optional'),
    ]

    operations = [
        migrations.RunPython(
            code=fix_notifications,
            reverse_code=migrations.RunPython.noop
        )
    ]
