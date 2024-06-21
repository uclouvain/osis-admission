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
from typing import Union

from django.contrib import messages
from django.http import HttpResponse, Http404
from django.utils.functional import cached_property
from django.utils.translation import gettext as _, get_language
from django.views.generic import TemplateView, FormView, RedirectView
from rest_framework.status import HTTP_204_NO_CONTENT

from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    EMPLACEMENTS_FAC,
    EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES,
    EMPLACEMENTS_SIC,
    EMPLACEMENTS_DOCUMENTS_RECLAMABLES,
    EMPLACEMENTS_DOCUMENTS_INTERNES,
    DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION,
)
from admission.ddd.admission.formation_continue import commands as continuing_education_commands
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.exports.admission_recap.admission_recap import admission_pdf_recap
from admission.forms.admission.document import (
    RequestFreeDocumentForm,
    RequestDocumentForm,
    ReplaceDocumentForm,
    UploadDocumentForm,
    RequestFreeDocumentWithDefaultFileForm,
    ChangeRequestDocumentForm,
    RetypeDocumentForm,
    UploadManagerDocumentForm,
)
from admission.infrastructure.utils import get_document_from_identifier, AdmissionDocument
from admission.constants import CONTEXT_GENERAL, CONTEXT_CONTINUING
from admission.views.common.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd import interface
from osis_common.utils.htmx import HtmxMixin
from osis_document.utils import get_file_url

__namespace__ = 'document'

__all__ = [
    'AnalysisFolderGenerationView',
    'DeleteDocumentView',
    'DocumentDetailView',
    'RequestCandidateDocumentView',
    'ReplaceDocumentView',
    'RequestFreeCandidateDocumentView',
    'RequestFreeCandidateDocumentWithDefaultFileView',
    'UploadDocumentByManagerView',
    'UploadFreeInternalDocumentView',
    'RequestStatusChangeDocumentView',
    'InProgressAnalysisFolderGenerationView',
    'RetypeDocumentView',
]


class UploadFreeInternalDocumentView(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    form_class = UploadManagerDocumentForm
    permission_required = 'admission.edit_documents'
    template_name = 'admission/document/upload_free_document.html'
    htmx_template_name = 'admission/document/upload_free_document.html'
    default_htmx_trigger_form_extra = {
        'refresh_list': True,
    }
    name = 'upload-free-document'
    urlpatterns = 'free-internal-upload'
    message_on_success = _('The document has been uploaded')
    prefix = 'upload-free-internal-document-form'
    commands = {
        CONTEXT_GENERAL: general_education_commands.InitialiserEmplacementDocumentLibreNonReclamableCommand,
        CONTEXT_CONTINUING: continuing_education_commands.InitialiserEmplacementDocumentLibreNonReclamableCommand,
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['context'] = self.current_context
        return kwargs

    @property
    def document_type(self):
        if self.is_continuing or self.is_fac:
            return TypeEmplacementDocument.LIBRE_INTERNE_FAC.name
        else:
            return TypeEmplacementDocument.LIBRE_INTERNE_SIC.name

    def form_valid(self, form) -> HttpResponse:
        document_id = message_bus_instance.invoke(
            self.commands[self.current_context](
                uuid_proposition=self.kwargs.get('uuid'),
                auteur=self.request.user.person.global_id,
                uuid_document=form.cleaned_data['file'][0],
                type_emplacement=self.document_type,
                libelle=form.cleaned_data['file_name_fr'],
            ),
        )
        self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant
        return super().form_valid(self.form_class(prefix=self.prefix, context=self.current_context))


class AnalysisFolderGenerationView(UploadFreeInternalDocumentView):
    name = 'analysis-folder-generation'
    urlpatterns = 'analysis-folder-generation'
    message_on_success = _('A new version of the analysis folder has been generated.')
    prefix = None  # No prefix for the form as it is not rendered in the template

    def get_form_kwargs(self):
        return {
            'context': self.current_context,
            'data': {
                'file_name': _('Analysis folder'),
                'file_0': admission_pdf_recap(self.admission, get_language(), with_annotated_documents=True),
            },
        }


def can_edit_document(document: AdmissionDocument, is_fac: bool, is_sic: bool, context: str) -> bool:
    """
    Check if the document can be edited by the person.
    For the general admissions:
    - FAC user can only update their own documents
    - SIC user can update all documents except the FAC and SYSTEM ones
    For the continuing admissions: FAC and SIC users can update all documents except the SYSTEM ones.
    """

    document_type = document.type

    if document_type == TypeEmplacementDocument.SYSTEME.name:
        return False

    if document_type in EMPLACEMENTS_FAC:
        return (is_fac and context == CONTEXT_GENERAL) or context == CONTEXT_CONTINUING

    if document_type in EMPLACEMENTS_SIC:
        return (is_sic and context == CONTEXT_GENERAL) or context == CONTEXT_CONTINUING

    return False


def can_retype_document(document: AdmissionDocument, document_identifier: str) -> bool:
    if document.type in EMPLACEMENTS_DOCUMENTS_INTERNES:
        return False
    if document_identifier in DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION:
        return False
    return True


class BaseRequestFreeCandidateDocument(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    permission_required = 'admission.edit_documents'
    default_htmx_trigger_form_extra = {
        'refresh_list': True,
    }
    commands = {
        CONTEXT_GENERAL: general_education_commands.InitialiserEmplacementDocumentLibreAReclamerCommand,
        CONTEXT_CONTINUING: continuing_education_commands.InitialiserEmplacementDocumentLibreAReclamerCommand,
    }

    @property
    def document_type(self):
        if self.is_continuing or self.is_fac:
            return TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name
        else:
            return TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['context'] = self.current_context
        return kwargs

    def form_valid(self, form) -> HttpResponse:
        document_id = message_bus_instance.invoke(
            self.commands[self.current_context](
                uuid_proposition=self.kwargs.get('uuid'),
                auteur=self.request.user.person.global_id,
                type_emplacement=self.document_type,
                libelle_en=form.cleaned_data['file_name_en'],
                libelle_fr=form.cleaned_data['file_name_fr'],
                raison=form.cleaned_data.get('reason', ''),
                uuid_document=form.cleaned_data['file'][0] if form.cleaned_data.get('file') else '',
                statut_reclamation=form.cleaned_data.get('request_status', ''),
                onglet_checklist_associe=form.cleaned_data.get('checklist_tab') or '',
            ),
        )
        self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant
        return super().form_valid(self.get_form())


class RequestFreeCandidateDocumentView(BaseRequestFreeCandidateDocument):
    form_class = RequestFreeDocumentForm
    template_name = 'admission/document/request_free_document.html'
    htmx_template_name = 'admission/document/request_free_document.html'
    urlpatterns = 'free-candidate-request'
    name = 'request-free-candidate-document'
    prefix = 'free-document-request-form'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['only_limited_request_choices'] = self.is_general & self.is_fac
        kwargs['candidate_language'] = self.admission.candidate.language
        return kwargs


class RequestFreeCandidateDocumentWithDefaultFileView(BaseRequestFreeCandidateDocument):
    form_class = RequestFreeDocumentWithDefaultFileForm
    template_name = 'admission/document/request_free_document_with_default_file.html'
    htmx_template_name = 'admission/document/request_free_document_with_default_file.html'
    urlpatterns = 'free-candidate-request-with-default-file'
    name = 'request-free-candidate-document-with-default-file'
    prefix = 'free-document-request-with-default-file-form'


class DocumentDetailView(LoadDossierViewMixin, HtmxPermissionRequiredMixin, HtmxMixin, TemplateView):
    template_name = 'admission/document/document_detail.html'
    htmx_template_name = 'admission/document/document_detail.html'
    permission_required = 'admission.view_documents_management'
    urlpatterns = {'detail': 'detail/<str:identifier>'}
    name = 'document-detail'

    def get_context_data(self, **kwargs):
        from osis_document.api.utils import get_remote_token
        from osis_document.api.utils import get_remote_metadata

        context = TemplateView().get_context_data(**kwargs)
        context['view'] = self

        # The identifier can be pass either through an url param or a query param.
        document_identifier = self.request.GET.get('identifier', self.kwargs.get('identifier'))

        document = get_document_from_identifier(self.admission, document_identifier)
        context['EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES'] = EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES

        if not document:
            return context

        context['document_identifier'] = document_identifier
        context['document_type'] = document.type
        context['requestable_document'] = document.requestable
        editable_document = can_edit_document(document, self.is_fac, self.is_sic, self.current_context)
        context['editable_document'] = editable_document
        context['retypable_document'] = can_retype_document(document, document_identifier)
        context['read_only_document'] = self.request.GET.get('read-only') == '1'
        context['document'] = document
        context['several_files'] = len(document.uuids) > 1

        if document.uuids:
            context['document_uuid'] = document.uuids[0]
            context['document_write_token'] = get_remote_token(
                uuid=context['document_uuid'],
                write_token=True,
                for_modified_upload=True,
            )
            context['document_metadata'] = get_remote_metadata(context['document_write_token'])

        # Request form
        request_initial = {
            'request_status': document.request_status,
            'reason': document.reason,
        }
        context['request_reason'] = document.reason

        context['request_form'] = RequestDocumentForm(
            candidate_language=self.admission.candidate.language,
            initial=request_initial,
            editable_document=editable_document,
            only_limited_request_choices=self.is_general and self.is_fac and document.type in EMPLACEMENTS_FAC,
        )

        context['retype_form'] = RetypeDocumentForm(admission_uuid=self.admission_uuid, identifier=document_identifier)
        context['replace_form'] = ReplaceDocumentForm(mimetypes=document.mimetypes, identifier=document_identifier)
        context['upload_form'] = UploadDocumentForm(mimetypes=document.mimetypes, identifier=document_identifier)

        return context


class DocumentFormView(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    default_htmx_trigger_form_extra = {
        'refresh_list': True,
    }
    commands = {
        CONTEXT_GENERAL: None,
        CONTEXT_CONTINUING: None,
    }
    permission_required = 'admission.edit_documents'
    name = 'document-action'
    close_modal_on_htmx_request = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_identifier'] = self.document_identifier
        context['document'] = self.document
        return context

    @property
    def command(self) -> Union[interface.QueryRequest, interface.CommandRequest]:
        command = self.commands.get(self.current_context)
        if command is None:
            raise Http404
        return command

    @property
    def document_identifier(self):
        return self.kwargs.get('identifier', '')

    @cached_property
    def document(self):
        return get_document_from_identifier(self.admission, self.document_identifier)

    def has_permission(self):
        # Check permission against the admission (only FAC and SIC users can access to it)
        has_permission = super().has_permission()

        if not self.document:
            raise Http404

        return has_permission and can_edit_document(self.document, self.is_fac, self.is_sic, self.current_context)


class RequestCandidateDocumentView(DocumentFormView):
    form_class = RequestDocumentForm
    template_name = 'admission/document/request_document.html'
    htmx_template_name = 'admission/document/request_document.html'
    urlpatterns = {'candidate-request': 'candidate-request/<str:identifier>'}
    request_commands = {
        CONTEXT_GENERAL: general_education_commands.ModifierReclamationEmplacementDocumentCommand,
        CONTEXT_CONTINUING: continuing_education_commands.ModifierReclamationEmplacementDocumentCommand,
    }
    cancel_commands = {
        CONTEXT_GENERAL: general_education_commands.AnnulerReclamationEmplacementDocumentCommand,
        CONTEXT_CONTINUING: continuing_education_commands.AnnulerReclamationEmplacementDocumentCommand,
    }

    @cached_property
    def editable_document(self):
        return can_edit_document(self.document, self.is_fac, self.is_sic, self.current_context)

    def has_permission(self):
        return super().has_permission() and self.document.requestable is True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['request_form'] = context['form']

        context['request_reason'] = (
            self.admission.requested_documents[self.document_identifier]['reason']
            if self.document_identifier in self.admission.requested_documents
            else ''
        )

        context['editable_document'] = self.editable_document

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['candidate_language'] = self.admission.candidate.language
        kwargs['editable_document'] = self.editable_document
        kwargs['only_limited_request_choices'] = (
            self.is_general and self.is_fac and self.document.type in EMPLACEMENTS_FAC
        )
        return kwargs

    def form_valid(self, form):
        if form.cleaned_data['request_status']:
            message_bus_instance.invoke(
                self.request_commands[self.current_context](
                    uuid_proposition=self.admission_uuid,
                    identifiant_emplacement=self.document_identifier,
                    raison=form.cleaned_data['reason'],
                    auteur=self.request.user.person.global_id,
                    statut_reclamation=form.cleaned_data['request_status'],
                )
            )
            if not self.document.request_status:
                self.message_on_success = _('The document has been designated as to be requested')
            elif self.document.request_status != form.cleaned_data['request_status']:
                self.message_on_success = _('The request status has been changed')
        else:
            document_id = message_bus_instance.invoke(
                self.cancel_commands[self.current_context](
                    uuid_proposition=self.admission_uuid,
                    identifiant_emplacement=self.document_identifier,
                    auteur=self.request.user.person.global_id,
                )
            )
            self.message_on_success = _('The document is no longer designated as to be requested')

            if self.document.type in EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES:
                self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant

        return super().form_valid(form)


class DeleteDocumentView(DocumentFormView):
    urlpatterns = {'delete': 'delete/<str:identifier>'}
    commands = {
        CONTEXT_GENERAL: general_education_commands.SupprimerEmplacementDocumentCommand,
        CONTEXT_CONTINUING: continuing_education_commands.SupprimerEmplacementDocumentCommand,
    }

    def delete(self, request, *args, **kwargs):
        document_id = message_bus_instance.invoke(
            self.command(
                uuid_proposition=self.admission_uuid,
                identifiant_emplacement=self.document_identifier,
                auteur=self.request.user.person.global_id,
            ),
        )

        if self.document:
            if self.document.type in EMPLACEMENTS_DOCUMENTS_RECLAMABLES:
                self.admission.update_requested_documents()
                self.htmx_trigger_form_extra['next'] = 'missing'

        self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant
        self.htmx_trigger_form_extra['refresh_list'] = True

        messages.success(self.request, _('The document has been deleted'))
        self.htmx_trigger_form(is_valid=True)

        return HttpResponse(status=HTTP_204_NO_CONTENT)


class RequestStatusChangeDocumentView(DocumentFormView):
    form_class = ChangeRequestDocumentForm
    urlpatterns = {'candidate-request-status': 'candidate-request-status/<str:identifier>'}
    template_name = 'admission/forms/default_form.html'
    htmx_template_name = 'admission/forms/default_form.html'
    default_htmx_trigger_form_extra = {
        'refresh_list': False,
        'keep_modal_open': True,
    }
    request_commands = {
        CONTEXT_GENERAL: general_education_commands.ModifierReclamationEmplacementDocumentCommand,
        CONTEXT_CONTINUING: continuing_education_commands.ModifierReclamationEmplacementDocumentCommand,
    }
    cancel_commands = {
        CONTEXT_GENERAL: general_education_commands.AnnulerReclamationEmplacementDocumentCommand,
        CONTEXT_CONTINUING: continuing_education_commands.AnnulerReclamationEmplacementDocumentCommand,
    }

    @cached_property
    def editable_document(self):
        return can_edit_document(self.document, self.is_fac, self.is_sic, self.current_context)

    def has_permission(self):
        return super().has_permission() and self.document.requestable is True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['document_identifier'] = self.document_identifier
        kwargs['proposition_uuid'] = self.admission_uuid
        kwargs['only_limited_request_choices'] = (
            self.is_general and self.is_fac and self.document.type in EMPLACEMENTS_FAC
        )
        kwargs['context'] = self.current_context
        return kwargs

    def form_valid(self, form):
        if form.cleaned_data[self.document_identifier]:
            message_bus_instance.invoke(
                self.request_commands[self.current_context](
                    uuid_proposition=self.admission_uuid,
                    identifiant_emplacement=self.document_identifier,
                    raison=self.document.reason,
                    auteur=self.request.user.person.global_id,
                    statut_reclamation=form.cleaned_data[self.document_identifier],
                )
            )
            self.message_on_success = _('The request status has been changed')
        else:
            message_bus_instance.invoke(
                self.cancel_commands[self.current_context](
                    uuid_proposition=self.admission_uuid,
                    identifiant_emplacement=self.document_identifier,
                    auteur=self.request.user.person.global_id,
                )
            )
            self.message_on_success = _('The document is no longer designated as to be requested')

        return super().form_valid(form)


class ReplaceDocumentView(DocumentFormView):
    form_class = ReplaceDocumentForm
    urlpatterns = {'replace': 'replace/<str:identifier>'}
    template_name = 'admission/document/replace_document.html'
    htmx_template_name = 'admission/document/replace_document.html'
    commands = {
        CONTEXT_GENERAL: general_education_commands.RemplacerEmplacementDocumentCommand,
        CONTEXT_CONTINUING: continuing_education_commands.RemplacerEmplacementDocumentCommand,
    }

    def post(self, request, *args, **kwargs) -> HttpResponse:
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['mimetypes'] = self.document.mimetypes
        kwargs['identifier'] = self.document_identifier
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['replace_form'] = context['form']
        return context

    def form_valid(self, form):
        document_id = message_bus_instance.invoke(
            self.command(
                uuid_proposition=self.admission_uuid,
                identifiant_emplacement=self.document_identifier,
                uuid_document=form.cleaned_data['file'][0],
                auteur=self.request.user.person.global_id,
            )
        )

        self.message_on_success = _('The document has been replaced')
        self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant

        return super().form_valid(
            self.form_class(
                mimetypes=self.document.mimetypes,
                identifier=self.document_identifier,
            )
        )


class UploadDocumentByManagerView(DocumentFormView):
    form_class = UploadDocumentForm
    urlpatterns = {'upload': 'upload/<str:identifier>'}
    template_name = 'admission/document/upload_document.html'
    htmx_template_name = 'admission/document/upload_document.html'
    commands = {
        CONTEXT_GENERAL: general_education_commands.RemplirEmplacementDocumentParGestionnaireCommand,
        CONTEXT_CONTINUING: continuing_education_commands.RemplirEmplacementDocumentParGestionnaireCommand,
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['mimetypes'] = self.document.mimetypes
        kwargs['identifier'] = self.document_identifier
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upload_form'] = context['form']
        return context

    def form_valid(self, form):
        document_id = message_bus_instance.invoke(
            self.command(
                uuid_proposition=self.admission_uuid,
                identifiant_emplacement=self.document_identifier,
                uuid_document=form.cleaned_data['file'][0],
                auteur=self.request.user.person.global_id,
            )
        )

        if self.document:
            if self.document.type == TypeEmplacementDocument.NON_LIBRE.name:
                self.admission.update_requested_documents()

            self.htmx_trigger_form_extra['next'] = (
                'received' if self.document.type in EMPLACEMENTS_DOCUMENTS_RECLAMABLES else 'uclouvain'
            )

        self.message_on_success = _('The document has been uploaded')
        self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant

        return super().form_valid(
            self.form_class(
                mimetypes=self.document.mimetypes,
                identifier=self.document_identifier,
            )
        )


class InProgressAnalysisFolderGenerationView(LoadDossierViewMixin, RedirectView):
    name = 'in-progress-analysis-folder-generation'
    permission_required = 'admission.generate_in_progress_analysis_folder'
    urlpatterns = 'in-progress-analysis-folder-generation'

    def get(self, request, *args, **kwargs):
        reading_token = admission_pdf_recap(self.admission, get_language(), with_annotated_documents=True)
        self.url = get_file_url(reading_token)
        return super().get(request, *args, **kwargs)


class RetypeDocumentView(DocumentFormView):
    form_class = RetypeDocumentForm
    urlpatterns = {'retype': 'retype/<str:identifier>'}
    template_name = 'admission/document/retype_form.html'
    htmx_template_name = 'admission/document/retype_form.html'
    commands = {
        CONTEXT_GENERAL: general_education_commands.RetyperDocumentCommand,
        CONTEXT_CONTINUING: continuing_education_commands.RetyperDocumentCommand,
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['admission_uuid'] = self.admission_uuid
        kwargs['identifier'] = self.document_identifier
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['retype_form'] = context['form']
        return context

    def form_valid(self, form):
        document_id = message_bus_instance.invoke(
            self.command(
                uuid_proposition=self.admission_uuid,
                identifiant_source=self.document_identifier,
                identifiant_cible=form.cleaned_data['identifier'],
                auteur=self.request.user.person.global_id,
            )
        )
        self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant
        return super().form_valid(form)
