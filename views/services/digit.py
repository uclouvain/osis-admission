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
import logging

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

__all__ = [
    "RequestDigitAccountCreationView",
    "SearchDigitAccountView",
    "UndoMergeAccountView",
    "DiscardMergeAccountView",
]

from django.views.generic import FormView
from django.views.generic.edit import ProcessFormView

from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.commands import DefairePropositionFusionCommand, \
    SoumettreTicketPersonneCommand, RefuserPropositionFusionCommand
from admission.utils import get_cached_general_education_admission_perm_obj
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal
from base.views.common import display_error_messages, display_success_messages

from osis_common.ddd.interface import BusinessException
from osis_role.contrib.views import PermissionRequiredMixin

logger = logging.getLogger(settings.DEFAULT_LOGGER)


class RequestDigitAccountCreationView(PermissionRequiredMixin, ProcessFormView):
    urlpatterns = {'request-digit-person-creation': 'request-digit-person-creation/<uuid:uuid>'}
    permission_required = "admission.merge_candidate_with_known_person"

    def post(self, request, *args, **kwargs):
        candidate = Person.objects.get(baseadmissions__uuid=kwargs['uuid'])
        response = redirect(request.META['HTTP_REFERER']) if request.META.get('HTTP_REFERER') else HttpResponse(
            status=200
        )

        if not self.base_admission.determined_academic_year:
            logger.info("[Digit] Envoi ticket Digit annulé - Pas d'année académique déterminée pour générer un NOMA")
            return redirect(request.META['HTTP_REFERER'])
        try:
            self.create_digit_person(global_id=candidate.global_id)
        except BusinessException as e:
            display_error_messages(request, "Une erreur est survenue lors de l'envoi dans DigIT")
            return response
        display_success_messages(
            request,
            "Ticket de création de compte envoyé avec succès dans DigIT"
        )
        return response

    @property
    def base_admission(self):
        return BaseAdmission.objects.get(uuid=self.kwargs['uuid'])

    @staticmethod
    def create_digit_person(global_id: str):
        from infrastructure.messages_bus import message_bus_instance
        message_bus_instance.invoke(
            SoumettreTicketPersonneCommand(global_id=global_id)
        )

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])


class SearchDigitAccountView(PermissionRequiredMixin, FormView):

    name = "search-account"

    urlpatterns = {'search-account': 'search-account/<uuid:uuid>'}
    permission_required = "admission.merge_candidate_with_known_person"

    def post(self, request, *args, **kwargs):
        candidate = Person.objects.get(baseadmissions__uuid=kwargs['uuid'])
        try:
            person_merge_proposal = PersonMergeProposal.objects.get(original_person__global_id=candidate.global_id)
            request.session['search_context'] = {'matches': person_merge_proposal.similarity_result}
            return redirect(
                reverse('admission:services:search-account-modal', kwargs={'uuid': kwargs['uuid']})
            )
        except PersonMergeProposal.DoesNotExist:
            display_error_messages(
                request,
                "Unable to find person merge proposal database object. Please contact technical team"
            )
            return redirect(to=self.request.META.get('HTTP_REFERER'))

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])


class UndoMergeAccountView(PermissionRequiredMixin, FormView):

    name = 'undo-merge'
    urlpatterns = {'undo-merge': 'undo-merge/<uuid:uuid>'}
    permission_required = "admission.merge_candidate_with_known_person"

    def post(self, request, *args, **kwargs):
        candidate = Person.objects.get(baseadmissions__uuid=kwargs['uuid'])

        from infrastructure.messages_bus import message_bus_instance

        message_bus_instance.invoke(
            DefairePropositionFusionCommand(
                global_id=candidate.global_id,
            )
        )

        return redirect(request.META['HTTP_REFERER'])

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])


class DiscardMergeAccountView(PermissionRequiredMixin, FormView):

    name = 'discard-merge'
    urlpatterns = {'discard-merge': 'discard-merge/<uuid:uuid>'}
    permission_required = "admission.merge_candidate_with_known_person"

    def post(self, request, *args, **kwargs):

        candidate = Person.objects.get(baseadmissions__uuid=kwargs['uuid'])

        from infrastructure.messages_bus import message_bus_instance

        message_bus_instance.invoke(
            RefuserPropositionFusionCommand(
                global_id=candidate.global_id,
            )
        )

        return HttpResponse(status=200, headers={'HX-Refresh': 'true'})

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])
