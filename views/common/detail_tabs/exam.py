# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import cached_property

from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.utils.translation import gettext as _

from admission.ddd.admission.dtos.examen import ExamenDTO
from admission.views.common.mixins import LoadDossierViewMixin

__all__ = [
    'ExamDetailView',
]

from osis_profile.models import Exam, EducationGroupYearExam
from osis_profile.models.enums.exam import ExamTypes


class ExamDetailView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'exam'
    template_name = 'admission/details/exams.html'
    permission_required = 'admission.view_admission_exam'

    def dispatch(self, *args, **kwargs):
        if self.education_group_year_exam is None:
            raise PermissionDenied(_("There is no required exam for this training."))
        return super().dispatch(*args, **kwargs)

    @cached_property
    def education_group_year_exam(self):
        return EducationGroupYearExam.objects.filter(education_group_year=self.admission.training).first()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        try:
            exam = Exam.objects.get(
                person=self.admission.candidate,
                type=ExamTypes.FORMATION.name,
                education_group_year_exam__education_group_year=self.admission.training,
            )
            context_data['examen'] = ExamenDTO(
                requis=self.education_group_year_exam is not None,
                attestation=exam.certificate,
                annee=exam.year.year if exam.year else None,
            )
        except Exam.DoesNotExist:
            context_data['examen'] = None
        context_data['education_group_year_exam'] = self.education_group_year_exam
        return context_data
