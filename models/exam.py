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
from django.db import models
from django.utils.translation import gettext_lazy as _

from osis_profile.models import Exam


class AdmissionExam(models.Model):
    admission = models.OneToOneField(
        'admission.BaseAdmission',
        verbose_name=_('Admission'),
        related_name='exam',
        on_delete=models.CASCADE,
    )
    exam = models.ForeignKey(
        # TODO try with Django 5.0+, with 'osis_profile.Exam' we do not have `admissions` available in the query
        Exam,
        verbose_name=_('Exam'),
        related_name='admissions',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"Exam {self.exam} of admission {self.admission}"
