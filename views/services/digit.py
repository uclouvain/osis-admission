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

import json

import requests
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

__all__ = [
    "RequestDigitAccountCreationView",
    "SearchDigitAccountView",
    "UndoMergeAccountView",
    "DiscardMergeAccountView",
]

from django.views.generic import FormView

from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.commands import RechercherCompteExistantQuery, DefairePropositionFusionCommand, \
    SoumettreTicketPersonneCommand, RefuserPropositionFusionCommand
from base.models.person import Person
from base.views.common import display_error_messages

from django.utils.translation import gettext_lazy as _


class RequestDigitAccountCreationView(FormView):

    urlpatterns = {'request-digit-person-creation': 'request-digit-person-creation/<uuid:uuid>'}

    def post(self, request, *args, **kwargs):
        candidate = Person.objects.get(baseadmissions__uuid=kwargs['uuid'])
        response = self.create_digit_person(candidate.global_id)
        return response

    @staticmethod
    def create_digit_person(global_id: str):
        from infrastructure.messages_bus import message_bus_instance
        return message_bus_instance.invoke(SoumettreTicketPersonneCommand(global_id=global_id))


class SearchDigitAccountView(FormView):

    urlpatterns = {'search-account': 'search-account/<uuid:uuid>'}

    def post(self, request, *args, **kwargs):

        candidate = Person.objects.get(baseadmissions__uuid=kwargs['uuid'])

        if self._is_valid_for_search(request, candidate):
            return redirect(to=self.request.META.get('HTTP_REFERER'))

        matches = search_digit_account(
            global_id=candidate.global_id,
            last_name=candidate.last_name,
            first_name=candidate.first_name,
            birth_date=str(candidate.birth_date)
        )

        request.session['search_context'] = {'matches': matches}
        return redirect(reverse('admission:services:search-account-modal', kwargs={'uuid': kwargs['uuid']}))

    @staticmethod
    def _is_valid_for_search(request, candidate):
        candidate_required_fields = [
            "last_name", "first_name", "birth_date",
        ]
        missing_fields = [field for field in candidate_required_fields if not getattr(candidate, field)]
        has_missing_fields = any(missing_fields)

        if has_missing_fields:
            display_error_messages(request, _(
                "Admission is not yet valid for searching UCLouvain. The following fields are required: "
            ) + ", ".join(missing_fields))

        return has_missing_fields


def search_digit_account(global_id: str, last_name: str, first_name: str, birth_date: str):
    from infrastructure.messages_bus import message_bus_instance

    return message_bus_instance.invoke(
        RechercherCompteExistantQuery(
            matricule=global_id, nom=last_name, prenom=first_name, date_naissance=birth_date
        )
    )


class UndoMergeAccountView(FormView):

    name = 'undo-merge'
    urlpatterns = {'undo-merge': 'undo-merge/<uuid:uuid>'}

    def post(self, request, *args, **kwargs):
        candidate = Person.objects.get(baseadmissions__uuid=kwargs['uuid'])

        from infrastructure.messages_bus import message_bus_instance

        message_bus_instance.invoke(
            DefairePropositionFusionCommand(
                global_id=candidate.global_id,
            )
        )

        return redirect(request.META['HTTP_REFERER'])


class DiscardMergeAccountView(FormView):

    name = 'discard-merge'
    urlpatterns = {'discard-merge': 'discard-merge/<uuid:uuid>'}

    def post(self, request, *args, **kwargs):

        candidate = Person.objects.get(baseadmissions__uuid=kwargs['uuid'])

        from infrastructure.messages_bus import message_bus_instance

        message_bus_instance.invoke(
            RefuserPropositionFusionCommand(
                global_id=candidate.global_id,
            )
        )

        return HttpResponse(status=200, headers={'HX-Refresh': 'true'})
