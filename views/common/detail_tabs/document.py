# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, FormView

from admission.auth.roles.program_manager import ProgramManager
from admission.ddd.admission.commands import (
    DeposerDocumentLibreParGestionnaireCommand,
    ReclamerDocumentLibreCommand,
    ReclamerDocumentCommand,
    AnnulerReclamationDocumentCommand,
)
from admission.ddd.admission.enums.emplacement_document import (
    DOCUMENTS_UCLOUVAIN,
    TypeDocument,
    StatutDocument,
)
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.forms.admission.document import UploadFreeDocumentForm, RequestFreeDocumentForm, RequestDocumentForm
from admission.infrastructure.utils import get_document_from_identifier
from admission.templatetags.admission import CONTEXT_GENERAL
from admission.views.doctorate.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin

__namespace__ = 'document'
__all__ = [
    'DocumentView',
    'UploadFreeCandidateDocumentView',
    'RequestFreeCandidateDocumentView',
    'DocumentDetailView',
    'RequestCandidateDocumentView',
]


class DocumentView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/document/base.html'
    permission_required = 'admission.view_documents_management'
    urlpatterns = {'document': ''}

    retrieve_documents_command = {
        CONTEXT_GENERAL: general_education_commands.RecupererDocumentsDemandeQuery,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['documents'] = (
            message_bus_instance.invoke(
                self.retrieve_documents_command[self.current_context](
                    uuid_demande=self.admission_uuid,
                )
            )
            if self.current_context in self.retrieve_documents_command
            else []
        )

        context['DOCUMENTS_UCLOUVAIN'] = DOCUMENTS_UCLOUVAIN

        return context


class UploadFreeCandidateDocumentView(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    form_class = UploadFreeDocumentForm
    template_name = 'admission/document/upload_free_document.html'
    htmx_template_name = 'admission/document/upload_free_document.html'
    urlpatterns = 'free-candidate-upload'
    permission_required = 'admission.view_documents_management'

    def form_valid(self, form) -> HttpResponse:
        message_bus_instance.invoke(
            DeposerDocumentLibreParGestionnaireCommand(
                uuid_demande=self.kwargs.get('uuid'),
                auteur=self.request.user.username,
                token_document=form.cleaned_data['file'][0],
                type_document=(
                    TypeDocument.CANDIDAT_FAC.name
                    if ProgramManager.belong_to(self.request.user.person)
                    else TypeDocument.CANDIDAT_SIC.name
                ),
                nom_document=form.cleaned_data['file_name'],
            ),
        )
        return self.render_to_response(
            self.get_context_data(
                form=self.form_class(),
                message=_('Document uploaded'),
            )
        )


class RequestFreeCandidateDocumentView(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    form_class = RequestFreeDocumentForm
    template_name = 'admission/document/request_free_document.html'
    htmx_template_name = 'admission/document/request_free_document.html'
    urlpatterns = 'free-candidate-request'
    permission_required = 'admission.view_documents_management'

    def form_valid(self, form) -> HttpResponse:
        message_bus_instance.invoke(
            ReclamerDocumentLibreCommand(
                uuid_demande=self.kwargs.get('uuid'),
                auteur=self.request.user.username,
                type_document=(
                    TypeDocument.CANDIDAT_FAC.name
                    if getattr(self.request.user, 'person', None) and ProgramManager.belong_to(self.request.user.person)
                    else TypeDocument.CANDIDAT_SIC.name
                ),
                nom_document=form.cleaned_data['file_name'],
                raison=form.cleaned_data['reason'],
            ),
        )
        return self.render_to_response(
            self.get_context_data(
                form=self.form_class(),
                message=_('Document requested'),
            )
        )


class DocumentDetailView(LoadDossierViewMixin, HtmxPermissionRequiredMixin, HtmxMixin, TemplateView):
    template_name = 'admission/document/document-detail.html'
    htmx_template_name = 'admission/document/document-detail.html'
    permission_required = 'admission.view_documents_management'
    urlpatterns = {'detail': 'detail/<str:identifier>'}

    def get_context_data(self, **kwargs):
        context = TemplateView().get_context_data(**kwargs)

        document_identifier = self.kwargs.get('identifier')

        document = get_document_from_identifier(self.admission, document_identifier)

        if document:
            context['document_identifier'] = document_identifier
            context['document_uuid'] = document.get('uuids')
            context['document_type'] = document.get('type')
            context['requestable_document'] = document.get('requestable')

        # Request form
        requested_document = self.admission.requested_documents.get(document_identifier)
        request_initial = None

        if requested_document:
            request_initial = {
                'is_requested': requested_document.get('status') == StatutDocument.A_RECLAMER.name,
                'reason': requested_document.get('reason'),
            }
            context['request_reason'] = requested_document.get('reason')

        context['request_form'] = RequestDocumentForm(
            candidate_language=self.admission.candidate.language,
            initial=request_initial,
        )

        return context


class RequestCandidateDocumentView(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    form_class = RequestDocumentForm
    template_name = 'admission/document/request_document.html'
    htmx_template_name = 'admission/document/request_document.html'
    permission_required = 'admission.view_documents_management'
    urlpatterns = {'candidate-request': 'candidate-request/<str:identifier>'}

    @property
    def document_identifier(self):
        return self.kwargs.get('identifier', '')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['request_form'] = context['form']

        requested_document = self.admission.requested_documents.get(self.document_identifier)

        if requested_document:
            context['request_reason'] = requested_document.get('reason')

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['candidate_language'] = self.admission.candidate.language
        return kwargs

    def form_valid(self, form):
        document = get_document_from_identifier(self.admission, self.document_identifier)

        if not document or not document.get('requestable'):
            self.message_on_failure = _('This document cannot be requested')
            return self.form_invalid(form)

        if form.cleaned_data['is_requested']:
            message_bus_instance.invoke(
                ReclamerDocumentCommand(
                    uuid_demande=self.kwargs.get('uuid'),
                    identifiant_document=self.document_identifier,
                    auteur=self.request.user.username,
                    type_document=document.get('type'),
                    raison=form.cleaned_data['reason'],
                )
            )
            self.message_on_success = _('The document has been designated as to be requested')
        else:
            message_bus_instance.invoke(
                AnnulerReclamationDocumentCommand(
                    uuid_demande=self.kwargs.get('uuid'),
                    identifiant_document=self.document_identifier,
                    type_document=document.get('type'),
                )
            )
            self.message_on_success = _('The document is no longer designated as to be requested')

        return super().form_valid(form)
