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
from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchVector
from django.db.models import Q, Exists, OuterRef, F

from admission.auth.roles.promoter import Promoter
from admission.auth.roles.candidate import Candidate
from base.auth.roles.tutor import Tutor
from base.models.person import Person

__all__ = [
    'CandidatesAutocomplete',
    'PromotersAutocomplete',
    'JuryMembersAutocomplete',
    'PersonAutocomplete',
    'TutorAutocomplete',
]

__namespace__ = False

from base.models.student import Student


class PersonsAutocomplete(LoginRequiredMixin):
    def get_results(self, context):
        return [
            {
                'id': person.get('global_id'),
                'text': ', '.join([person.get('last_name'), person.get('first_name')]),
            }
            for person in context['object_list']
        ]


class CandidatesAutocomplete(PersonsAutocomplete, autocomplete.Select2QuerySetView):
    urlpatterns = 'candidates'

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        return (
            Candidate.objects.annotate(
                name=SearchVector(
                    'person__first_name',
                    'person__last_name',
                ),
            )
            .filter(
                Q(name=q)
                | Q(person__email__icontains=q)
                | Q(person__private_email__icontains=q)
                | Q(person__student__registration_id__icontains=q)
            )
            .order_by('person__last_name', 'person__first_name')
            .values(
                first_name=F('person__first_name'),
                last_name=F('person__last_name'),
                global_id=F('person__global_id'),
            )
            .distinct()
            if q
            else []
        )


class PromotersAutocomplete(PersonsAutocomplete, autocomplete.Select2QuerySetView):
    urlpatterns = 'promoters'

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        qs = (
            Person.objects.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(global_id__icontains=q))
            .filter(Exists(Promoter.objects.filter(person=OuterRef('pk'))))  # Is a promoter
            .order_by('last_name', 'first_name')
            .values(
                'first_name',
                'last_name',
                'global_id',
            )
        )
        return qs if q else []


class JuryMembersAutocomplete(PersonsAutocomplete, autocomplete.Select2QuerySetView):
    urlpatterns = 'jury-members'

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        qs = (
            Person.objects.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(global_id__icontains=q))
            .exclude(Exists(Student.objects.filter(person=OuterRef('pk'))))
            .order_by('last_name', 'first_name')
            .values(
                'first_name',
                'last_name',
                'global_id',
            )
        )
        return qs if q else []


class PersonAutocomplete(PersonsAutocomplete, autocomplete.Select2QuerySetView):
    urlpatterns = 'person'

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        qs = (
            Person.objects.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(global_id__icontains=q))
            .exclude(Q(user_id__isnull=True) | Q(global_id=''))
            .exclude(Exists(Student.objects.filter(person=OuterRef('pk'))))
            .order_by('last_name', 'first_name')
            .values(
                'first_name',
                'last_name',
                'global_id',
            )
        )
        return qs if q else []


class TutorAutocomplete(PersonsAutocomplete, autocomplete.Select2QuerySetView):
    urlpatterns = 'tutor'

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        qs = (
            Tutor.objects.annotate(
                first_name=F("person__first_name"),
                last_name=F("person__last_name"),
                global_id=F("person__global_id"),
            )
            .filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(global_id__icontains=q))
            .exclude(Q(person__user_id__isnull=True) | Q(person__global_id=''))
            .distinct('global_id')
            .values(
                'first_name',
                'last_name',
                'global_id',
            )
        )
        return qs if q else []
