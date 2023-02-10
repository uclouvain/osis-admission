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

from django.core.management import BaseCommand
from django.utils.timezone import now

from admission.exports.admission_archive import admission_pdf_archive
from admission.exports.admission_canvas import admission_pdf_canvas
from admission.exports.admission_confirmation_success_attestation import admission_confirmation_success_attestation
from admission.contrib.models import AdmissionTask
from osis_async.models.enums import TaskStates
from osis_async.utils import update_task


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Get all unprocessed admission tasks
        task_list = (
            AdmissionTask.objects.filter(task__state=TaskStates.PENDING.name)
            .order_by('-task__created_at')
            .values_list('task__uuid', 'type')
        )
        errors = []
        for task_uuid, task_type in task_list:
            update_task(task_uuid, progression=0, state=TaskStates.PROCESSING, started_at=now())
            try:
                if task_type == AdmissionTask.TaskType.ARCHIVE.name:
                    admission_pdf_archive(task_uuid)
                elif task_type == AdmissionTask.TaskType.CANVAS.name:
                    admission_pdf_canvas(task_uuid)
                elif task_type == AdmissionTask.TaskType.CONFIRMATION_SUCCESS.name:
                    admission_confirmation_success_attestation(task_uuid)
                update_task(task_uuid, progression=100, state=TaskStates.DONE, completed_at=now())
            except Exception as e:
                update_task(task_uuid, progression=0, state=TaskStates.PENDING)
                errors.append(e)

        if errors:
            # Raise the first error to have a FAILED status on task
            raise errors[0]
