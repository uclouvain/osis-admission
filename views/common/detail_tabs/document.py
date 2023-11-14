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

from django.contrib import messages
from django.http import HttpResponse, Http404
from django.utils.functional import cached_property
from django.utils.translation import gettext as _, get_language
from django.views.generic import TemplateView, FormView
from rest_framework.status import HTTP_204_NO_CONTENT

from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.program_manager import ProgramManager
from admission.auth.roles.sic_management import SicManagement
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    StatutEmplacementDocument,
    EMPLACEMENTS_FAC,
    EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES,
    EMPLACEMENTS_SIC,
    EMPLACEMENTS_DOCUMENTS_RECLAMABLES,
)
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.exports.admission_recap.admission_recap import admission_pdf_recap
from admission.forms.admission.document import (
    UploadFreeDocumentForm,
    RequestFreeDocumentForm,
    RequestDocumentForm,
    ReplaceDocumentForm,
    UploadDocumentForm,
    RequestFreeDocumentWithDefaultFileForm,
)
from admission.infrastructure.utils import get_document_from_identifier, AdmissionDocument
from admission.views.doctorate.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.models.person import Person
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin


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
]


class UploadFreeInternalDocumentView(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    form_class = UploadFreeDocumentForm
    permission_required = 'admission.view_documents_management'
    template_name = 'admission/document/upload_free_document.html'
    htmx_template_name = 'admission/document/upload_free_document.html'
    default_htmx_trigger_form_extra = {
        'refresh_list': True,
    }
    name = 'upload-free-document'
    urlpatterns = 'free-internal-upload'
    message_on_success = _('The document has been uploaded')

    @property
    def document_type(self):
        return (
            TypeEmplacementDocument.LIBRE_INTERNE_FAC.name
            if ProgramManager.belong_to(self.request.user.person)
            else TypeEmplacementDocument.LIBRE_INTERNE_SIC.name
        )

    def form_valid(self, form) -> HttpResponse:
        document_id = message_bus_instance.invoke(
            general_education_commands.InitialiserEmplacementDocumentLibreNonReclamableCommand(
                uuid_proposition=self.kwargs.get('uuid'),
                auteur=self.request.user.person.global_id,
                uuid_document=form.cleaned_data['file'][0],
                type_emplacement=self.document_type,
                libelle=form.cleaned_data['file_name'],
            ),
        )
        self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant
        return super().form_valid(self.form_class())


class AnalysisFolderGenerationView(UploadFreeInternalDocumentView):
    name = 'analysis-folder-generation'
    urlpatterns = 'analysis-folder-generation'
    message_on_success = _('A new version of the analysis folder has been generated.')

    def get_form_kwargs(self):
        return {
            'data': {
                'file_name': _('Analysis folder'),
                'file_0': admission_pdf_recap(self.admission, get_language(), with_annotated_documents=True),
            }
        }


def can_edit_document(person: Person, document: AdmissionDocument) -> bool:
    """
    Check if the document can be edited by the person.
    - FAC user can only update their own documents
    - SIC user can update all documents except the FAC and SYSTEM ones
    """

    document_type = document.type

    if document_type == TypeEmplacementDocument.SYSTEME.name:
        return False

    if document_type in EMPLACEMENTS_FAC:
        return ProgramManager.belong_to(person=person)

    if document_type in EMPLACEMENTS_SIC:
        return SicManagement.belong_to(person) or CentralManager.belong_to(person)

    return False


class BaseRequestFreeCandidateDocument(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    permission_required = 'admission.view_documents_management'
    default_htmx_trigger_form_extra = {
        'refresh_list': True,
    }

    def form_valid(self, form) -> HttpResponse:
        document_id = message_bus_instance.invoke(
            general_education_commands.InitialiserEmplacementDocumentLibreAReclamerCommand(
                uuid_proposition=self.kwargs.get('uuid'),
                auteur=self.request.user.person.global_id,
                type_emplacement=(
                    TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name
                    if ProgramManager.belong_to(self.request.user.person)
                    else TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name
                ),
                libelle=form.cleaned_data['file_name'],
                raison=form.cleaned_data['reason'],
                uuid_document=form.cleaned_data['file'][0] if form.cleaned_data.get('file') else '',
            ),
        )
        self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant
        return super().form_valid(self.form_class())


class RequestFreeCandidateDocumentView(BaseRequestFreeCandidateDocument):
    form_class = RequestFreeDocumentForm
    template_name = 'admission/document/request_free_document.html'
    htmx_template_name = 'admission/document/request_free_document.html'
    urlpatterns = 'free-candidate-request'
    name = 'request-free-candidate-document'


class RequestFreeCandidateDocumentWithDefaultFileView(BaseRequestFreeCandidateDocument):
    form_class = RequestFreeDocumentWithDefaultFileForm
    template_name = 'admission/document/request_free_document_with_default_file.html'
    htmx_template_name = 'admission/document/request_free_document_with_default_file.html'
    urlpatterns = 'free-candidate-request-with-default-file'
    name = 'request-free-candidate-document-with-default-file'


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

        # The identifier can be pass either through an url param or a query param.
        document_identifier = self.request.GET.get('identifier', self.kwargs.get('identifier'))

        document = get_document_from_identifier(self.admission, document_identifier)
        context['EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES'] = EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES

        if not document:
            return context

        context['document_identifier'] = document_identifier
        context['document_type'] = document.type
        context['requestable_document'] = document.requestable
        editable_document = can_edit_document(self.request.user.person, document)
        context['editable_document'] = editable_document

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
            'is_requested': document.status == StatutEmplacementDocument.A_RECLAMER.name,
            'reason': document.reason,
        }
        context['request_reason'] = document.reason

        context['request_form'] = RequestDocumentForm(
            candidate_language=self.admission.candidate.language,
            initial=request_initial,
            auto_requested=document.automatically_required,
            editable_document=editable_document,
        )

        context['replace_form'] = ReplaceDocumentForm(mimetypes=document.mimetypes)
        context['upload_form'] = UploadDocumentForm(mimetypes=document.mimetypes)

        return context


class DocumentFormView(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    default_htmx_trigger_form_extra = {
        'refresh_list': True,
    }
    permission_required = 'admission.view_documents_management'
    name = 'document-action'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_identifier'] = self.document_identifier
        return context

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

        return has_permission and can_edit_document(self.request.user.person, self.document)


class RequestCandidateDocumentView(DocumentFormView):
    form_class = RequestDocumentForm
    template_name = 'admission/document/request_document.html'
    htmx_template_name = 'admission/document/request_document.html'
    urlpatterns = {'candidate-request': 'candidate-request/<str:identifier>'}

    @cached_property
    def editable_document(self):
        return can_edit_document(self.request.user.person, self.document)

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
        kwargs['auto_requested'] = self.document.automatically_required
        kwargs['editable_document'] = self.editable_document
        return kwargs

    def form_valid(self, form):
        if form.cleaned_data['is_requested']:
            message_bus_instance.invoke(
                general_education_commands.ModifierReclamationEmplacementDocumentCommand(
                    uuid_proposition=self.admission_uuid,
                    identifiant_emplacement=self.document_identifier,
                    raison=form.cleaned_data['reason'],
                    auteur=self.request.user.person.global_id,
                )
            )
            self.message_on_success = _('The document has been designated as to be requested')
        else:
            document_id = message_bus_instance.invoke(
                general_education_commands.AnnulerReclamationEmplacementDocumentCommand(
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

    def delete(self, request, *args, **kwargs):
        document_id = message_bus_instance.invoke(
            general_education_commands.SupprimerEmplacementDocumentCommand(
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


class ReplaceDocumentView(DocumentFormView):
    form_class = ReplaceDocumentForm
    urlpatterns = {'replace': 'replace/<str:identifier>'}
    template_name = 'admission/document/replace_document.html'
    htmx_template_name = 'admission/document/replace_document.html'

    def post(self, request, *args, **kwargs) -> HttpResponse:
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['mimetypes'] = self.document.mimetypes
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['replace_form'] = context['form']
        return context

    def form_valid(self, form):
        document_id = message_bus_instance.invoke(
            general_education_commands.RemplacerEmplacementDocumentCommand(
                uuid_proposition=self.admission_uuid,
                identifiant_emplacement=self.document_identifier,
                uuid_document=form.cleaned_data['file'][0],
                auteur=self.request.user.person.global_id,
            )
        )

        self.message_on_success = _('The document has been replaced')
        self.htmx_trigger_form_extra['refresh_details'] = document_id.identifiant

        return super().form_valid(self.form_class(mimetypes=self.document.mimetypes))


class UploadDocumentByManagerView(DocumentFormView):
    form_class = UploadDocumentForm
    urlpatterns = {'upload': 'upload/<str:identifier>'}
    template_name = 'admission/document/upload_document.html'
    htmx_template_name = 'admission/document/upload_document.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['mimetypes'] = self.document.mimetypes
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upload_form'] = context['form']
        return context

    def form_valid(self, form):
        document_id = message_bus_instance.invoke(
            general_education_commands.RemplirEmplacementDocumentParGestionnaireCommand(
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

        return super().form_valid(self.form_class(mimetypes=self.document.mimetypes))
