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
from admission.ddd.admission.commands import RechercherCompteExistantCommand, DefairePropositionFusionCommand, \
    SoumettreTicketPersonneCommand, RefuserPropositionFusionCommand
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.views.common import display_error_messages, display_success_messages

from django.utils.translation import gettext_lazy as _

from osis_common.ddd.interface import BusinessException
from osis_role.contrib.views import PermissionRequiredMixin

logger = logging.getLogger(settings.DEFAULT_LOGGER)


class RequestDigitAccountCreationView(ProcessFormView, PermissionRequiredMixin):

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
            self.create_digit_person(
                global_id=candidate.global_id,
                year=self.base_admission.determined_academic_year.year,
            )
        except BusinessException as e:
            display_error_messages(request, "Une erreur est survenue lors de l'envoi dans DigIT")
            return response

        display_success_messages(request, "Ticket de création de compte envoyé avec succès dans DigIT")

        return response

    @property
    def base_admission(self):
        return BaseAdmission.objects.get(uuid=self.kwargs['uuid'])

    @staticmethod
    def create_digit_person(global_id: str, year: int):
        from infrastructure.messages_bus import message_bus_instance
        message_bus_instance.invoke(
            SoumettreTicketPersonneCommand(
                global_id=global_id,
                annee=year,
            )
        )


class SearchDigitAccountView(FormView, PermissionRequiredMixin):

    name = "search-account"

    urlpatterns = {'search-account': 'search-account/<uuid:uuid>'}
    permission_required = "admission.merge_candidate_with_known_person"

    def post(self, request, *args, **kwargs):

        candidate = Person.objects.get(baseadmissions__uuid=kwargs['uuid'])
        person_merge_proposal = self._get_person_merge_proposal(candidate)

        if self._is_valid_for_search(request, candidate):
            return redirect(to=self.request.META.get('HTTP_REFERER'))

        if person_merge_proposal and person_merge_proposal.status == PersonMergeStatus.PENDING.name:
            matches = person_merge_proposal.similarity_result
        else:
            matches = search_digit_account(
                global_id=candidate.global_id,
                last_name=candidate.last_name,
                first_name=candidate.first_name,
                other_first_name=candidate.middle_name,
                birth_date=str(candidate.birth_date) if candidate.birth_date else "",
                sex=candidate.sex,
                niss=candidate.national_number,
            )

        request.session['search_context'] = {'matches': matches}
        return redirect(reverse('admission:services:search-account-modal', kwargs={'uuid': kwargs['uuid']}))

    @staticmethod
    def _is_valid_for_search(request, candidate):
        candidate_required_fields = [
            "last_name", "first_name",
        ]
        missing_fields = [field for field in candidate_required_fields if not getattr(candidate, field)]
        has_missing_fields = any(missing_fields)

        if has_missing_fields:
            display_error_messages(request, _(
                "Admission is not yet valid for searching UCLouvain account. The following fields are required: "
            ) + ", ".join(missing_fields))

        return has_missing_fields

    def _get_person_merge_proposal(self, candidate):
        try:
            return PersonMergeProposal.objects.get(original_person__global_id=candidate.global_id)
        except PersonMergeProposal.DoesNotExist:
            return None


def search_digit_account(
        global_id: str,
        last_name: str,
        first_name: str,
        other_first_name: str,
        birth_date: str,
        sex: str,
        niss: str,
):
    from infrastructure.messages_bus import message_bus_instance

    return message_bus_instance.invoke(
        RechercherCompteExistantCommand(
            matricule=global_id,
            nom=last_name,
            prenom=first_name,
            date_naissance=birth_date,
            autres_prenoms=other_first_name,
            niss=niss,
            genre=sex,
        )
    )


class UndoMergeAccountView(FormView, PermissionRequiredMixin):

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


class DiscardMergeAccountView(FormView, PermissionRequiredMixin):

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
