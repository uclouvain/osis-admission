# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import attr
from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, resolve_url
from django.views.generic.edit import FormView
from django.utils.translation import gettext_lazy as _
from rest_framework.settings import api_settings

from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.admission.doctorat.preparation.commands import (
    RenvoyerInvitationSignatureExterneCommand,
    DemanderSignaturesCommand,
    ApprouverPropositionParPdfCommand,
    DesignerPromoteurReferenceCommand,
    ModifierMembreSupervisionExterneCommand,
    SupprimerMembreCACommand,
    SupprimerPromoteurCommand,
    GetGroupeDeSupervisionCommand,
    VerifierProjetQuery,
    IdentifierMembreCACommand,
    IdentifierPromoteurCommand,
    RedonnerLaMainAuCandidatCommand,
)
from admission.forms.admission.doctorate.supervision import (
    DoctorateAdmissionSupervisionForm,
    DoctorateAdmissionMemberSupervisionForm,
    DoctorateAdmissionApprovalByPdfForm,
    ACTOR_EXTERNAL,
    EXTERNAL_FIELDS,
)
from admission.utils import get_cached_admission_perm_obj, gather_business_exceptions
from admission.views.common.mixins import LoadDossierViewMixin
from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from base.views.common import display_error_messages, display_info_messages
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin

__namespace__ = None

__all__ = [
    "DoctorateAdmissionAddActorFormView",
    "DoctorateAdmissionRemoveActorFormView",
    "DoctorateAdmissionEditExternalMemberFormView",
    "DoctorateAdmissionSetReferencePromoterFormView",
    "DoctorateAdmissionApprovalByPdfFormView",
    "DoctorateAdmissionExternalResendFormView",
    "DoctorateAdmissionRequestSignaturesView",
    "DoctorateAdmissionSendBackToTheCandidateView",
]


class DoctorateAdmissionAddActorFormView(LoadDossierViewMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = {'supervision': 'supervision'}
    form_class = DoctorateAdmissionSupervisionForm
    template_name = 'admission/doctorate/details/supervision.html'

    def get_permission_required(self):
        if self.request.method == 'GET':
            return ('admission.view_admission_supervision',)
        return ('admission.add_supervision_member',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['signature_conditions'] = gather_business_exceptions(
            VerifierProjetQuery(uuid_proposition=self.kwargs['uuid'])
        ).get(api_settings.NON_FIELD_ERRORS_KEY, [])
        context['groupe_supervision'] = message_bus_instance.invoke(
            GetGroupeDeSupervisionCommand(uuid_proposition=self.admission_uuid)
        )
        context['approve_by_pdf_form'] = DoctorateAdmissionApprovalByPdfForm()
        context['add_form'] = context.pop('form')  # Trick template to not add button
        return context

    def prepare_data(self, data):
        is_external = data.pop('internal_external') == ACTOR_EXTERNAL
        promoter = data.pop('tutor')
        ca_member = data.pop('person')
        matricule = (ca_member if data['type'] == ActorType.CA_MEMBER.name else promoter) if not is_external else ""
        if not is_external:
            # Remove data about external actor
            data = {**data, **{f: '' for f in EXTERNAL_FIELDS}}
        return {
            'matricule_auteur': self.request.user.person.global_id,
            'type': data['type'],
            'matricule': matricule,
            **data,
        }

    def call_command(self, form):
        data = self.prepare_data(form.cleaned_data)
        if data.pop('type') == ActorType.CA_MEMBER.name:
            command = IdentifierMembreCACommand
        else:
            command = IdentifierPromoteurCommand

        message_bus_instance.invoke(
            command(
                uuid_proposition=self.admission_uuid,
                **data,
            )
        )

    def get_success_url(self):
        return resolve_url('admission:doctorate:supervision', uuid=self.kwargs['uuid'])


class DoctorateAdmissionRemoveActorFormView(LoadDossierViewMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = {'remove-actor': 'supervision/remove-member/<type>/<uuid_membre>'}
    form_class = forms.Form
    permission_required = 'admission.remove_supervision_member'
    template_name = 'admission/doctorate/forms/supervision/remove_actor.html'
    actor_type_mapping = {
        ActorType.PROMOTER.name: ('signatures_promoteurs', 'promoteur'),
        ActorType.CA_MEMBER.name: ('signatures_membres_CA', 'membre_CA'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            supervision = message_bus_instance.invoke(
                GetGroupeDeSupervisionCommand(uuid_proposition=self.kwargs['uuid'])
            )
            supervision = attr.asdict(supervision)
            context['member'] = self.get_member(supervision)
        except (AttributeError, KeyError):
            raise Http404(_('Member not found'))
        return context

    def get_member(self, supervision):
        collection_name, attr_name = self.actor_type_mapping[self.kwargs['type']]
        for signature in supervision[collection_name]:
            member = signature[attr_name]
            if member['uuid'] == self.kwargs['uuid_membre']:
                return member
        raise KeyError

    def prepare_data(self, data):
        return {
            'uuid_proposition': self.kwargs['uuid'],
            'matricule_auteur': self.request.user.person.global_id,
        }

    def call_command(self, form):
        data = self.prepare_data(form.cleaned_data)
        if self.kwargs['type'] == ActorType.CA_MEMBER.name:
            data['uuid_membre_ca'] = self.kwargs['uuid_membre']
            command = SupprimerMembreCACommand
        else:
            data['uuid_promoteur'] = self.kwargs['uuid_membre']
            command = SupprimerPromoteurCommand
        message_bus_instance.invoke(command(**data))

    def get_success_url(self):
        return resolve_url('admission:doctorate:supervision', uuid=self.kwargs['uuid'])


class DoctorateAdmissionEditExternalMemberFormView(PermissionRequiredMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = {'edit-external-member': 'edit-external-member/<uuid_membre>'}
    form_class = DoctorateAdmissionMemberSupervisionForm
    permission_required = 'admission.edit_external_supervision_member'

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs.get('uuid'))

    def get(self, request, *args, **kwargs):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def prepare_data(self, data):
        return {'uuid_proposition': self.kwargs['uuid'], 'uuid_membre': self.kwargs['uuid_membre'], **data}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['prefix'] = f"member-{self.kwargs['uuid_membre']}"
        return kwargs

    def call_command(self, form):
        data = self.prepare_data(form.cleaned_data)
        message_bus_instance.invoke(
            ModifierMembreSupervisionExterneCommand(matricule_auteur=self.request.user.person.global_id, **data)
        )

    def get_success_url(self):
        return resolve_url('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def form_invalid(self, form):
        display_error_messages(self.request, (
            _("Please correct the errors below"),
            str(form.errors),
        ))
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])


class DoctorateAdmissionSetReferencePromoterFormView(PermissionRequiredMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = {'set-reference-promoter': 'set-reference-promoter/<uuid_promoteur>'}
    form_class = forms.Form
    permission_required = 'admission.add_supervision_member'

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs.get('uuid'))

    def get(self, request, *args, **kwargs):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def prepare_data(self, data):
        return {
            'uuid_proposition': str(self.kwargs['uuid']),
            'uuid_promoteur': self.kwargs['uuid_promoteur'],
        }

    def call_command(self, form):
        data = self.prepare_data(form.cleaned_data)
        message_bus_instance.invoke(
            DesignerPromoteurReferenceCommand(
                matricule_auteur=self.request.user.person.global_id,
                **data,
            )
        )

    def get_success_url(self):
        return resolve_url('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def form_invalid(self, form):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])


class DoctorateAdmissionApprovalByPdfFormView(PermissionRequiredMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = 'approve-by-pdf'
    form_class = DoctorateAdmissionApprovalByPdfForm
    permission_required = 'admission.approve_proposition_by_pdf'

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs.get('uuid'))

    def get(self, request, *args, **kwargs):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def call_command(self, form):
        data = form.cleaned_data
        message_bus_instance.invoke(
            ApprouverPropositionParPdfCommand(
                uuid_proposition=str(self.kwargs["uuid"]),
                matricule_auteur=self.request.user.person.global_id,
                **data,
            )
        )

    def get_success_url(self):
        return resolve_url('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def form_invalid(self, form):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])


class DoctorateAdmissionExternalResendFormView(PermissionRequiredMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = {'resend-invite': 'resend-invite/<uuid_membre>'}
    template_name = 'admission/doctorate/forms/external_confirm.html'
    permission_required = 'admission.approve_proposition_by_pdf'
    form_class = forms.Form

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs.get('uuid'))

    def get(self, request, *args, **kwargs):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def prepare_data(self, data):
        return {
            'uuid_proposition': str(self.kwargs['uuid']),
            'uuid_membre': self.kwargs['uuid_membre'],
        }

    def call_command(self, form):
        data = self.prepare_data(form.cleaned_data)
        message_bus_instance.invoke(RenvoyerInvitationSignatureExterneCommand(**data))

    def get_success_url(self):
        display_info_messages(self.request, _("An invitation has been sent again."))
        return resolve_url('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def form_invalid(self, form):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])


class DoctorateAdmissionRequestSignaturesView(PermissionRequiredMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = 'request-signatures'
    form_class = forms.Form
    permission_required = 'admission.request_signatures'

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs.get('uuid'))

    def get(self, request, *args, **kwargs):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def call_command(self, form):
        message_bus_instance.invoke(
            DemanderSignaturesCommand(
                uuid_proposition=str(self.kwargs["uuid"]),
                matricule_auteur=self.request.user.person.global_id,
            )
        )

    def get_success_url(self):
        display_info_messages(self.request, _("Signature requests sent"))
        return resolve_url('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def form_invalid(self, form):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])


class DoctorateAdmissionSendBackToTheCandidateView(PermissionRequiredMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = 'send-back-to-candidate'
    form_class = forms.Form
    permission_required = 'admission.change_admission_project'

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs.get('uuid'))

    def get(self, request, *args, **kwargs):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def call_command(self, form):
        message_bus_instance.invoke(
            RedonnerLaMainAuCandidatCommand(
                uuid_proposition=str(self.kwargs["uuid"]),
                matricule_gestionnaire=self.request.user.person.global_id,
            )
        )

    def get_success_url(self):
        display_info_messages(self.request, _("Admission sent back to the candidate"))
        return resolve_url('admission:doctorate:supervision', uuid=self.kwargs['uuid'])

    def form_invalid(self, form):
        return redirect('admission:doctorate:supervision', uuid=self.kwargs['uuid'])
