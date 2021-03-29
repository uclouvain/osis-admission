from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from base.models.person import Person


class PersonAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Person.objects.all()
        if self.q:
            qs = qs.filter(
                Q(email__icontains=self.q) | Q(last_name__icontains=self.q)
            )
        return qs.order_by("last_name", "first_name")

    def get_result_label(self, result: Person):
        return "{person.last_name} {person.first_name} ({person.email})".format(
            person=result
        )


class CandidateAutocomplete(PersonAutocomplete):
    def get_queryset(self):
        qs = Person.objects.filter(admissions__isnull=False)
        if self.q:
            qs = qs.filter(
                Q(email__icontains=self.q) | Q(last_name__icontains=self.q)
            )
        return qs.order_by("last_name", "first_name").distinct()
