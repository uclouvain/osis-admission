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
from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Exists, OuterRef

from admission.auth.roles.promoter import Promoter
from admission.auth.roles.candidate import Candidate
from base.models.person import Person


class PersonsAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        return Person.objects.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(global_id__icontains=q)
        ).order_by('last_name', 'first_name').values(
            'first_name',
            'last_name',
            'global_id',
        ) if q else []

    def get_results(self, context):
        return [
            {
                'id': person.get('global_id'),
                'text': ', '.join([person.get('last_name'), person.get('first_name')]),
            } for person in context['object_list']
        ]


class CandidatesAutocomplete(PersonsAutocomplete):

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        return Person.objects.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(student__registration_id__icontains=q)
        ).annotate(
            has_admission=Exists(Candidate.objects.filter(person=OuterRef('pk'))),
        ).filter(
            has_admission=True,
        ).order_by('last_name', 'first_name').values(
            'first_name',
            'last_name',
            'global_id',
        ) if q else []


class PromotersAutocomplete(PersonsAutocomplete):
    def get_queryset(self):
        q = self.request.GET.get('q', '')

        return Person.objects.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(global_id__icontains=q)
        ).annotate(
            is_promoter=Exists(Promoter.objects.filter(person=OuterRef('pk'))),
        ).filter(
            is_promoter=True,
        ).order_by('last_name', 'first_name').values(
            'first_name',
            'last_name',
            'global_id',
        ) if q else []
