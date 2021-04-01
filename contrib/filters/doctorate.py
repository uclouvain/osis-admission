import django_filters as filters
from dal import autocomplete
from django.utils.translation import gettext_lazy as _

from admission.contrib.models import AdmissionDoctorate
from base.models.person import Person


class AdmissionDoctorateFilter(filters.FilterSet):
    candidate = filters.ModelChoiceFilter(
        queryset=Person.objects.filter(admissions__isnull=False).distinct(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="admissions:candidate-autocomplete",
            attrs={
                "data-theme": "bootstrap",
                "data-placeholder": _("Indicate the last name or email"),
            }
        ),
        label=_("Candidate"),
    )

    class Meta:
        model = AdmissionDoctorate
        fields = [
            "type",
            "candidate",
        ]
