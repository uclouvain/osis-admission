# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.shortcuts import resolve_url
from django.views import generic
from django.views.generic.edit import FormMixin

from admission.models.doctoral_training import Activity
from admission.ddd.parcours_doctoral.formation.commands import AccepterActivitesCommand, SoumettreActivitesCommand
from admission.ddd.parcours_doctoral.formation.domain.model.enums import StatutActivite
from admission.forms.doctorate.training.activity import get_category_labels
from admission.forms.doctorate.training.processus import BatchActivityForm
from admission.templatetags.admission import can_read_tab
from admission.constants import CONTEXT_DOCTORATE

__all__ = [
    "ComplementaryTrainingView",
    "CourseEnrollmentView",
    "DoctoralTrainingActivityView",
    "TrainingRedirectView",
]

__namespace__ = False

from admission.views.common.mixins import LoadDossierViewMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance


class TrainingRedirectView(LoadDossierViewMixin, generic.RedirectView):
    urlpatterns = {'training': 'training'}
    """Redirect depending on the status of CDD and admission type"""

    def get_redirect_url(self, *args, **kwargs):
        if can_read_tab(CONTEXT_DOCTORATE, 'doctoral-training', self.admission):
            return resolve_url('admission:doctorate:doctoral-training', uuid=self.admission_uuid)
        if can_read_tab(CONTEXT_DOCTORATE, 'complementary-training', self.admission):
            return resolve_url('admission:doctorate:complementary-training', uuid=self.admission_uuid)
        return resolve_url('admission:doctorate:course-enrollment', uuid=self.admission_uuid)


class TrainingListMixin(LoadDossierViewMixin, FormMixin):
    form_class = BatchActivityForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = self.get_queryset()
        context['categories'] = get_category_labels(self.admission.doctorate.management_entity_id)
        context['statuses'] = StatutActivite.choices
        return context

    def get_success_url(self):
        return self.request.get_full_path()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['doctorate_id'] = self.get_permission_object().pk
        return kwargs

    def form_valid(self, form):
        activity_ids = [activite.uuid for activite in form.cleaned_data['activity_ids']]
        if '_accept' in self.request.POST:
            cmd = AccepterActivitesCommand(
                doctorat_uuid=self.admission_uuid,
                activite_uuids=activity_ids,
            )
        else:
            cmd = SoumettreActivitesCommand(
                doctorat_uuid=self.admission_uuid,
                activite_uuids=activity_ids,
            )
        try:
            form.activities_in_error = []
            message_bus_instance.invoke(cmd)
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
                form.activities_in_error.append(exception.activite_id.uuid)
            return super().form_invalid(form)
        return super().form_valid(form)


class DoctoralTrainingActivityView(TrainingListMixin, generic.FormView):  # pylint: disable=too-many-ancestors
    """List view for doctoral training activities"""

    urlpatterns = {'doctoral-training': 'doctoral-training'}
    template_name = "admission/doctorate/cdd/training_list.html"
    permission_required = "admission.view_doctoral_training"

    def get_queryset(self):
        return Activity.objects.for_doctoral_training(self.admission_uuid)


class ComplementaryTrainingView(TrainingListMixin, generic.FormView):  # pylint: disable=too-many-ancestors
    urlpatterns = {'complementary-training': 'complementary-training'}
    template_name = "admission/doctorate/cdd/complementary_training_list.html"
    permission_required = 'admission.view_complementary_training'

    def get_queryset(self):
        return Activity.objects.for_complementary_training(self.admission_uuid)


class CourseEnrollmentView(TrainingListMixin, generic.FormView):  # pylint: disable=too-many-ancestors
    urlpatterns = {'course-enrollment': 'course-enrollment'}
    template_name = "admission/doctorate/cdd/course_enrollment.html"
    permission_required = 'admission.view_course_enrollment'

    def get_queryset(self):
        return Activity.objects.for_enrollment_courses(self.admission_uuid)
