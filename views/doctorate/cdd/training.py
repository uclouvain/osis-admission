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
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, resolve_url
from django.views import generic

from admission.contrib.models.doctoral_training import Activity
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import CategorieActivite, StatutActivite
from admission.forms.doctorate.training.activity import (
    CommunicationForm,
    ConferenceCommunicationForm,
    ConferenceForm,
    ConferencePublicationForm,
    PublicationForm,
    ResidencyCommunicationForm,
    ResidencyForm,
    ServiceForm,
    SeminarForm,
    SeminarCommunicationForm,
    ValorisationForm,
)
from admission.views.doctorate.mixins import LoadDossierViewMixin


class DoctorateTrainingActivityView(LoadDossierViewMixin, generic.TemplateView):
    template_name = "admission/doctorate/cdd/training_list.html"
    permission_required = "admission.change_activity"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Activity.objects.filter(doctorate__uuid=self.kwargs['pk'])
        context['activities'] = qs.prefetch_related('children')
        context['categories'] = CategorieActivite.choices
        context['counts'] = qs.aggregate(
            validated=Count('pk', filter=Q(status=StatutActivite.ACCEPTEE.name)),
            pending=Count('pk', filter=Q(status=StatutActivite.SOUMISE.name)),
        )
        context['categories_count'] = qs.values('category').annotate(
            unsubmitted=Count('pk', filter=Q(status=StatutActivite.NON_SOUMISE.name)),
            submitted=Count('pk', filter=Q(status=StatutActivite.SOUMISE.name)),
            validated=Count('pk', filter=Q(status=StatutActivite.ACCEPTEE.name)),
        )
        return context


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
        base_url = resolve_url("admission:doctorate:training", pk=self.kwargs['pk'])
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
