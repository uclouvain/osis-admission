##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from osis_document_components.fields import FileField

from admission.models.base import admission_directory_path


def answer_directory_path(specific_question_answer: 'SpecificQuestionAnswer', filename: str):
    return admission_directory_path(specific_question_answer.admission, filename)


class SpecificQuestionAnswer(models.Model):

    admission = models.ForeignKey(
        'admission.BaseAdmission',
        verbose_name=_('Admission'),
        related_name='specific_question_answers',
        on_delete=models.CASCADE,
    )

    form_item = models.ForeignKey(
        'admission.AdmissionFormItem',
        verbose_name=_('Admission'),
        on_delete=models.PROTECT,
    )

    file = FileField(
        verbose_name=_('File'),
        upload_to=answer_directory_path,
        blank=True,
        null=True,
    )

    answer = models.JSONField(
        verbose_name=_('Answer'),
        encoder=DjangoJSONEncoder,
        blank=True,
        null=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['admission', 'form_item'], name='admission_specific_question_answers_unique'
            ),
            models.CheckConstraint(
                condition=Q(file__isnull=False) | Q(answer__isnull=False),
                name='admission_specific_question_answers_file_or_answer',
            ),
        ]
