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

from django.db.models import Q, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, resolve_url
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from admission.contrib.models.doctoral_training import Activity
from admission.ddd.doctorat.formation.commands import (
    AccepterActivitesCommand,
    RefuserActiviteCommand,
    SoumettreActivitesCommand,
)
from admission.ddd.doctorat.formation.domain.model._enums import CategorieActivite, StatutActivite
from admission.forms.doctorate.training.activity import *
from admission.forms.doctorate.training.activity import get_category_labels
from admission.forms.doctorate.training.processus import BatchActivityForm, RefuseForm
from admission.views.doctorate.mixins import LoadDossierViewMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance


class DoctorateTrainingActivityView(LoadDossierViewMixin, generic.FormView):
    template_name = "admission/doctorate/cdd/training_list.html"
    permission_required = "admission.change_activity"
    form_class = BatchActivityForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Activity.objects.filter(doctorate__uuid=self.admission_uuid)
        context['activities'] = qs.prefetch_related('children')
        context['categories'] = get_category_labels(self.admission.doctorate.management_entity_id)
        context['statuses'] = StatutActivite.choices
        context['counts'] = qs.aggregate(
            total=Sum('ects'),
            validated=Sum('ects', filter=Q(status=StatutActivite.ACCEPTEE.name)),
            pending=Sum('ects', filter=Q(status=StatutActivite.SOUMISE.name)),
        )
        context['categories_count'] = qs.values('category').annotate(
            unsubmitted=Sum('ects', filter=Q(status=StatutActivite.NON_SOUMISE.name)),
            submitted=Sum('ects', filter=Q(status=StatutActivite.SOUMISE.name)),
            validated=Sum('ects', filter=Q(status=StatutActivite.ACCEPTEE.name)),
        )
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


class DoctorateTrainingActivityFormMixin(LoadDossierViewMixin):
    template_name = "admission/doctorate/forms/training.html"
    model = Activity
    permission_required = "admission.change_activity"
    form_class_mapping = {
        CategorieActivite.CONFERENCE: ConferenceForm,
        (CategorieActivite.CONFERENCE, CategorieActivite.COMMUNICATION): ConferenceCommunicationForm,
        (CategorieActivite.CONFERENCE, CategorieActivite.PUBLICATION): ConferencePublicationForm,
        CategorieActivite.RESIDENCY: ResidencyForm,
        (CategorieActivite.RESIDENCY, CategorieActivite.COMMUNICATION): ResidencyCommunicationForm,
        CategorieActivite.COMMUNICATION: CommunicationForm,
        CategorieActivite.PUBLICATION: PublicationForm,
        CategorieActivite.SERVICE: ServiceForm,
        CategorieActivite.SEMINAR: SeminarForm,
        (CategorieActivite.SEMINAR, CategorieActivite.COMMUNICATION): SeminarCommunicationForm,
        CategorieActivite.VAE: ValorisationForm,
        CategorieActivite.COURSE: CourseForm,
        CategorieActivite.PAPER: PaperForm,
    }

    def get_form_class(self):
        try:
            form_class = self.form_class_mapping[self.get_category()]
        except KeyError as e:
            raise Http404(f"No form mapped: {e}")
        return form_class

    def get_category(self):
        category = CategorieActivite[self.kwargs['category'].upper()]
        if self.request.GET.get('parent'):
            parent = get_object_or_404(Activity, uuid=self.request.GET.get('parent'))
            return CategorieActivite[parent.category], category
        return category

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['admission'] = self.get_permission_object()
        return kwargs

    def get_success_url(self):
        base_url = resolve_url("admission:doctorate:training", uuid=self.admission_uuid)
        return f"{base_url}#{self.object.uuid}"


class DoctorateTrainingActivityAddView(DoctorateTrainingActivityFormMixin, generic.CreateView):
    object = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        params = {'doctorate': kwargs['admission'], 'category': self.kwargs['category'].upper()}
        if self.request.GET.get('parent'):
            params['parent'] = get_object_or_404(Activity, uuid=self.request.GET.get('parent'))
        self.object = kwargs['instance'] = Activity(**params)
        return kwargs


class DoctorateTrainingActivityEditView(DoctorateTrainingActivityFormMixin, generic.UpdateView):
    slug_field = 'uuid'
    pk_url_kwarg = None
    slug_url_kwarg = 'activity_id'

    def get_category(self):
        category = CategorieActivite[self.object.category]
        if self.object.parent_id:
            return CategorieActivite[self.object.parent.category], category
        return category

    @property
    def activity(self):
        # Don't remove, this is to share same template code in front-office
        return self.object


class DoctorateTrainingActivityDeleteView(LoadDossierViewMixin, generic.DeleteView):
    model = Activity
    permission_required = "admission.delete_activity"
    slug_field = 'uuid'
    pk_url_kwarg = "NOT_TO_BE_USED"
    slug_url_kwarg = 'activity_id'
    template_name = "admission/doctorate/forms/training/activity_confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        Activity.objects.filter(
            Q(uuid=self.kwargs['activity_id']) | Q(parent__uuid=self.kwargs['activity_id'])
        ).delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return resolve_url("admission:doctorate:training", uuid=self.admission_uuid)


class DoctorateTrainingActivityRefuseView(LoadDossierViewMixin, SingleObjectMixin, generic.FormView):
    model = Activity
    permission_required = "admission.refuse_activity"
    slug_field = 'uuid'
    pk_url_kwarg = "NOT_TO_BE_USED"
    slug_url_kwarg = 'activity_id'
    template_name = "admission/doctorate/forms/training/activity_refuse.html"
    form_class = RefuseForm
    avec_modification = False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    @property
    def activity(self):
        # Don't remove, this is to share same template code in front-office
        return self.object

    def form_valid(self, form):
        message_bus_instance.invoke(
            RefuserActiviteCommand(
                doctorat_uuid=self.admission_uuid,
                activite_uuid=self.kwargs['activity_id'],
                avec_modification=self.avec_modification,
                remarque=form.cleaned_data['reason'],
            )
        )
        return super().form_valid(form)

    def get_success_url(self):
        return resolve_url("admission:doctorate:training", uuid=self.admission_uuid)


class DoctorateTrainingActivityRequireChangesView(DoctorateTrainingActivityRefuseView):
    avec_modification = True
    template_name = "admission/doctorate/forms/training/activity_require_changes.html"
