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

# Import .py file which contains tasks to be executed
from celery.schedules import crontab

from backoffice.celery import app as celery_app
from . import check_academic_calendar
from . import process_admission_tasks
from . import retrieve_digit_tickets_status
from . import retry_digit_duplicates_finding

tasks = {
    'Generate admission files': {
        'task': 'admission.tasks.process_admission_tasks.run',
        'schedule': crontab(),  # this runs every minute
    },
    '|Admission| Check academic calendar': {
        'task': 'admission.tasks.check_academic_calendar.run',
        'schedule': crontab(minute=0, hour=0, day_of_month='*', month_of_year='*', day_of_week=0),
    },
    '|Admission| Retrieve digit person tickets status': {
        'task': 'admission.tasks.retrieve_digit_tickets_status.run',
        'schedule': crontab(minute='*/5'),
    },
    '|Admission| Retry digit duplicates finding': {
        'task': 'admission.tasks.retry_digit_duplicates_finding.run',
        'schedule': crontab(minute='*/5'),
    },
    # couvre le basculement de la période de création de compte dans DigIT
    # '|Admission| Bulk create digit persons tickets': {
    #     'task': 'admission.tasks.bulk_create_digit_persons_tickets.run',
    #     'schedule': crontab(minute=0, hour=0, day_of_month='1', month_of_year='*'),
    # }
}

celery_app.conf.beat_schedule.update(tasks)
