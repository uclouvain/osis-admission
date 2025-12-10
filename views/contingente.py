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
from django.core.files.temp import NamedTemporaryFile
from django.http import Http404, FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.functional import cached_property
from django.views import View
from django.views.generic import TemplateView, DetailView, UpdateView
from openpyxl import Workbook

from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.forms.admission.contingente import ContingenteTrainingForm
from admission.models.contingente import ContingenteTraining
from base.models.academic_calendar import AcademicCalendar
from base.models.education_group_year import EducationGroupYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.utils.utils import format_academic_year

__namespace__ = 'contingente'

__all__ = [
    "ContingenteManageView",
    "ContingenteTrainingManageView",
    "ContingenteTrainingUpdateView",
    "ContingenteTrainingExportView",
]


class ContingenteMixin:
    @cached_property
    def academic_year(self):
        today = timezone.now().date()
        return AcademicCalendar.objects.get(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date__lte=today,
            end_date__gte=today,
        ).data_year


class ContingenteManageView(ContingenteMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'admission.view_contingente_management'
    template_name = 'admission/general_education/contingente/manage.html'
    urlpatterns = {'index': ''}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academic_year'] = format_academic_year(self.academic_year, short=True)
        context['publication_calendar'] = AcademicCalendar.objects.filter(
            reference=AcademicCalendarTypes.ADMISSION_NON_RESIDENT_QUOTA_RESULT_PUBLICATION.name,
            data_year=self.academic_year,
        ).first()
        context['trainings'] = SIGLES_WITH_QUOTA
        return context


class ContingenteTrainingManageView(ContingenteMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'admission.view_contingente_management'
    template_name = 'admission/general_education/contingente/manage_training.html'
    urlpatterns = 'training'
    
    def dispatch(self, request, *args, **kwargs):
        if request.GET.get('training') not in SIGLES_WITH_QUOTA:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['academic_year'] = format_academic_year(self.academic_year, short=True)
        context['training'] = self.request.GET.get('training')
        contingente_training, _ = ContingenteTraining.objects.get_or_create(
            training=EducationGroupYear.objects.get(acronym=self.request.GET.get('training'), academic_year=self.academic_year),
        )
        context['contingente_training'] = contingente_training
        context['contingente_training_form'] = ContingenteTrainingForm(instance=contingente_training)

        return context


class ContingenteTrainingUpdateView(ContingenteMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'admission.view_contingente_management'
    template_name = 'admission/general_education/contingente/contingente_training_form.html'
    urlpatterns = {'training_change': 'training/<str:training>'}
    form_class = ContingenteTrainingForm
    
    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            return redirect('admission:contingente:index')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(
            ContingenteTraining,
            training__acronym=self.kwargs['training'],
            training__academic_year=self.academic_year,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contingente_training_form'] = context['form']
        return context

    def form_valid(self, form):
        form.save()
        return self.render_to_response(self.get_context_data(contingente_training_form_success=True))


class ContingenteTrainingExportView(ContingenteMixin, PermissionRequiredMixin, View):
    permission_required = 'admission.view_contingente_management'
    urlpatterns = {'training_export': 'training/<str:training>/export'}

    def get(self, request, *args, **kwargs):
        contingente_training = get_object_or_404(
            ContingenteTraining,
            training__acronym=self.kwargs['training'],
            training__academic_year=self.academic_year,
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "New Title"
        tmp = NamedTemporaryFile()
        wb.save(tmp.name)
        tmp.seek(0)
        return FileResponse(tmp, as_attachment=True, filename='contingente.xlsx', content_type='application/vnd.ms-excel')
