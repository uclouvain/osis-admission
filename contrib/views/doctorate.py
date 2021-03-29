from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, CreateView
from django_filters.views import FilterView

from admission.contrib.filters import AdmissionDoctorateFilter
from admission.contrib.forms import AdmissionDoctorateCreateForm
from admission.contrib.models import AdmissionDoctorate
from admission.contrib.serializers import AdmissionDoctorateSerializer
from base.utils.search import SearchMixin


class AdmissionDoctorateCreateView(CreateView):
    model = AdmissionDoctorate
    template_name = "admission/doctorate/admission_doctorate_create.html"
    form_class = AdmissionDoctorateCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user
        if user.is_authenticated and hasattr(user, "person"):
            # Add user.person to the form kwargs and do the logic in the form
            kwargs.update({"author": user.person})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("admissions:doctorate-list")
        return context


class AdmissionDoctorateDetailView(DetailView):
    model = AdmissionDoctorate
    template_name = "admission/doctorate/admission_doctorate_detail.html"


class AdmissionDoctorateListView(SearchMixin, FilterView):
    model = AdmissionDoctorate
    template_name = "admission/doctorate/admission_doctorate_list.html"
    context_object_name = "doctorates"
    filterset_class = AdmissionDoctorateFilter
    serializer_class = AdmissionDoctorateSerializer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["paginator"].count == 0 and self.request.GET:
            messages.add_message(self.request, messages.WARNING, _("No result!"))
            # FIXME When getting no results, the warning message above is well displayed
            # But doing a research that is returning results just after still shows the message
        context.update({
            "items_per_page": context["paginator"].per_page,
        })
        return context
