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

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.functional import cached_property
from django.views.generic import TemplateView, DetailView

from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.models.contingente import ContingenteTraining
from base.models.academic_calendar import AcademicCalendar
from base.models.education_group_year import EducationGroupYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.utils.utils import format_academic_year

__namespace__ = 'contingente'

__all__ = [
    "ContingenteManageView",
    "ContingenteTrainingManageView",
]



class ContingenteManageView(PermissionRequiredMixin, TemplateView):
    permission_required = 'admission.view_contingente_management'
    template_name = 'admission/general_education/contingente/manage.html'
    urlpatterns = {'index': ''}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        academic_year = AcademicCalendar.objects.get(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date__lte=today,
            end_date__gte=today,
        ).data_year
        context['academic_year'] = format_academic_year(academic_year, short=True)
        context['publication_calendar'] = AcademicCalendar.objects.filter(
            reference=AcademicCalendarTypes.ADMISSION_NON_RESIDENT_QUOTA_RESULT_PUBLICATION.name,
            data_year=academic_year,
        ).first()
        context['trainings'] = SIGLES_WITH_QUOTA
        return context


class ContingenteTrainingManageView(PermissionRequiredMixin, TemplateView):
    permission_required = 'admission.view_contingente_management'
    template_name = 'admission/general_education/contingente/manage_training.html'
    urlpatterns = 'training'
    
    def dispatch(self, request, *args, **kwargs):
        if request.GET.get('training') not in SIGLES_WITH_QUOTA:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()
        academic_year = AcademicCalendar.objects.get(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date__lte=today,
            end_date__gte=today,
        ).data_year
        context['academic_year'] = format_academic_year(academic_year, short=True)
        context['training'] = self.request.GET.get('training')
        contingente_training, _ = ContingenteTraining.objects.get_or_create(
            training=EducationGroupYear.objects.get(acronym=self.request.GET.get('training'), academic_year=academic_year),
        )
        context['contingente_training'] = contingente_training

        return context
