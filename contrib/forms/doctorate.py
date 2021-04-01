from dal import autocomplete
from django import forms

from admission.contrib.models import AdmissionDoctorate
from base.models.person import Person


class AdmissionDoctorateCreateForm(forms.ModelForm):
    candidate = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        widget=autocomplete.ModelSelect2(url="admissions:person-autocomplete"),
    )

    def __init__(self, *args, **kwargs):
        # Retrieve the author passed from the view by get_form_kwargs
        self.author = kwargs.pop("author", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.author = self.author
        return super().save()

    class Meta:
        model = AdmissionDoctorate
        fields = [
            "type",
            "candidate",
            "comment",
        ]
