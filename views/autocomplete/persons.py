# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import json

from dal import autocomplete
from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.contrib.postgres.search import SearchVector
from django.db.models import Exists, F, OuterRef, Q
from django.utils.decorators import method_decorator

from admission.admission_utils.get_actor_option_text import get_actor_option_text
from admission.auth.roles.candidate import Candidate
from admission.ddd.admission.doctorat.preparation.commands import (
    RechercherPromoteursQuery,
)
from admission.ddd.admission.doctorat.preparation.dtos import PromoteurDTO
from base.auth.roles.tutor import Tutor
from base.models.person import Person
from base.models.student import Student
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'CandidatesAutocomplete',
    'JuryMembersAutocomplete',
    'PersonAutocomplete',
    'PromotersAutocomplete',
    'TutorAutocomplete',
]

__namespace__ = False


class PersonsAutocomplete:
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


class JuryMembersAutocomplete(PersonsAutocomplete, autocomplete.Select2QuerySetView):
    urlpatterns = 'jury-members'

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        qs = (
            Person.objects.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(global_id__icontains=q))
            .exclude(Exists(Student.objects.filter(person=OuterRef('pk'), person__tutor__isnull=True)))
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

    def get_results(self, context):
        return [
            {
                'id': person.get('global_id'),
                'text': '%(last_name)s, %(first_name)s (%(email)s)' % person,
            }
            for person in context['object_list']
        ]

    def get_queryset(self):
        q = self.request.GET.get('q', '')
        qs = Person.objects
        if q:
            qs = qs.filter(
                *[
                    Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(global_id__icontains=term)
                    for term in q.split()
                ],
            )
        qs = (
            qs.exclude(Q(first_name='') | Q(last_name=''))
            .filter(
                # Keep only persons with internal account and email address
                global_id__startswith='0',
                email__endswith=settings.INTERNAL_EMAIL_SUFFIX,
            )
            .exclude(Exists(Student.objects.filter(person=OuterRef('pk'), person__tutor__isnull=True)))
            .order_by('last_name', 'first_name')
            .values(
                'first_name',
                'last_name',
                'email',
                'global_id',
            )
        )
        return qs


class TutorAutocomplete(PersonsAutocomplete, autocomplete.Select2QuerySetView):
    urlpatterns = 'tutor'

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        qs = Tutor.objects
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(global_id__icontains=q))
        qs = (
            qs.annotate(
                first_name=F("person__first_name"),
                last_name=F("person__last_name"),
                global_id=F("person__global_id"),
            )
            .filter(
                # Keep only persons with internal account and email address
                global_id__startswith='0',
                email__endswith=settings.INTERNAL_EMAIL_SUFFIX,
            )
            .distinct()
            .values(
                'first_name',
                'last_name',
                'global_id',
            )
            .order_by('last_name', 'first_name')
        )
        return qs


class PromotersAutocomplete(autocomplete.Select2ListView):
    urlpatterns = 'promoters'

    def autocomplete_results(self, results):
        # The list is already filtered
        return results

    def results(self, results):
        if not self.q:
            return []

        results_without_duplicates = []
        already_added_actors: set[str] = set()

        promoters: list[PromoteurDTO] = message_bus_instance.invoke(RechercherPromoteursQuery(terme_recherche=self.q))

        for actor in promoters:
            promoter_as_dict = {
                'global_id': actor.matricule,
                'first_name': actor.prenom,
                'last_name': actor.nom,
            }
            identifier_str = json.dumps(promoter_as_dict)

            # Create only one option for external members having the same name
            if identifier_str not in already_added_actors:
                already_added_actors.add(identifier_str)
                results_without_duplicates.append(
                    {
                        'id': identifier_str,
                        'text': get_actor_option_text(promoter_as_dict),
                    }
                )

        return results_without_duplicates
