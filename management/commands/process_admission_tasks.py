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
from osis_async.models.enums import TaskState
from osis_async.utils import update_task

from admission.contrib.models import AdmissionTask
from admission.exports.admission_archive import admission_pdf_archive
from admission.exports.admission_canvas import admission_pdf_canvas
from admission.exports.admission_confirmation_success_attestation import admission_confirmation_success_attestation
from admission.exports.admission_recap.admission_async_recap import (
    general_education_admission_pdf_recap_from_task,
    continuing_education_admission_pdf_recap_from_task,
    doctorate_education_admission_pdf_recap_from_task,
)
from admission.tasks.merge_admission_documents import (
    general_education_admission_document_merging_from_task,
    continuing_education_admission_document_merging_from_task,
    doctorate_education_admission_document_merging_from_task,
)


class Command(BaseCommand):
    task_operation_by_type = {
        AdmissionTask.TaskType.ARCHIVE.name: admission_pdf_archive,
        AdmissionTask.TaskType.CANVAS.name: admission_pdf_canvas,
        AdmissionTask.TaskType.CONFIRMATION_SUCCESS.name: admission_confirmation_success_attestation,
        AdmissionTask.TaskType.GENERAL_RECAP.name: general_education_admission_pdf_recap_from_task,
        AdmissionTask.TaskType.CONTINUING_RECAP.name: continuing_education_admission_pdf_recap_from_task,
        AdmissionTask.TaskType.DOCTORATE_RECAP.name: doctorate_education_admission_pdf_recap_from_task,
        AdmissionTask.TaskType.GENERAL_MERGE.name: general_education_admission_document_merging_from_task,
        AdmissionTask.TaskType.CONTINUING_MERGE.name: continuing_education_admission_document_merging_from_task,
        AdmissionTask.TaskType.DOCTORATE_MERGE.name: doctorate_education_admission_document_merging_from_task,
    }

    def handle(self, *args, **options):
        # Get all unprocessed admission tasks
        task_list = (
            AdmissionTask.objects.filter(task__state=TaskState.PENDING.name)
            .order_by('-task__created_at')
            .values_list('task__uuid', 'type')
        )
        errors = []
        for task_uuid, task_type in task_list:
            update_task(task_uuid, progression=0, state=TaskState.PROCESSING, started_at=now())
            try:
                if task_type in self.task_operation_by_type:
                    self.task_operation_by_type[task_type](task_uuid)
                update_task(task_uuid, progression=100, state=TaskState.DONE, completed_at=now())
            except Exception as e:
                update_task(task_uuid, progression=0, state=TaskState.PENDING)
                errors.append(e)

        if errors:
            # Raise the first error to have a FAILED status on task
            raise errors[0]
