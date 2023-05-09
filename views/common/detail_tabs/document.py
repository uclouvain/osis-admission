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
import datetime

from django.conf import settings
from django.http import HttpResponse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, FormView
from osis_mail_template.models import MailTemplate

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
from admission.ddd.admission.formation_generale.commands import (
    ReclamerDocumentsAuCandidatParFACCommand,
    ReclamerDocumentsAuCandidatParSICCommand,
)
from admission.forms.admission.document import (
    UploadFreeDocumentForm,
    RequestFreeDocumentForm,
    RequestDocumentForm,
    RequestAllDocumentsForm,
)
from admission.infrastructure.utils import get_document_from_identifier
from admission.mail_templates import (
    ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_GENERAL,
    ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_CONTINUING,
    ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_GENERAL,
    ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_DOCTORATE,
    ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_DOCTORATE,
    ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_CONTINUING,
)
from admission.templatetags.admission import CONTEXT_GENERAL, CONTEXT_DOCTORATE, CONTEXT_CONTINUING
from admission.utils import format_academic_year
from admission.views.doctorate.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.models.entity_version import EntityVersion
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin

__namespace__ = 'document'
__all__ = [
    'DocumentView',
    'UploadFreeCandidateDocumentView',
    'UploadFreeInternalDocumentView',
    'RequestFreeCandidateDocumentView',
    'DocumentDetailView',
    'RequestCandidateDocumentView',
]


class DocumentView(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    template_name = 'admission/document/base.html'
    htmx_template_name = 'admission/document/request_all_documents.html'
    permission_required = 'admission.view_documents_management'
    urlpatterns = {'document': ''}
    form_class = RequestAllDocumentsForm

    retrieve_documents_command = {
        CONTEXT_GENERAL: general_education_commands.RecupererDocumentsDemandeQuery,
    }

    @cached_property
    def is_fac(self):
        return getattr(self.request.user, 'person', None) is not None and ProgramManager.belong_to(
            self.request.user.person
        )

    @cached_property
    def deadline(self):
        return datetime.date.today() + datetime.timedelta(days=15)

    @cached_property
    def documents(self):
        return (
            message_bus_instance.invoke(
                self.retrieve_documents_command[self.current_context](
                    uuid_demande=self.admission_uuid,
                )
            )
            if self.current_context in self.retrieve_documents_command
            else []
        )

    @cached_property
    def requestable_documents(self):
        documents_to_exclude = TypeDocument.CANDIDAT_SIC.name if self.is_fac else TypeDocument.CANDIDAT_FAC.name
        return [
            document
            for document in self.documents
            if document.statut == StatutDocument.A_RECLAMER.name and document.type != documents_to_exclude
        ]

    def get_initial(self):
        email_object, email_content = self.get_email_template()

        return {
            'deadline': self.deadline,
            'message_object': email_object,
            'message_content': email_content,
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['documents'] = self.requestable_documents
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['documents'] = self.documents
        context['DOCUMENTS_UCLOUVAIN'] = DOCUMENTS_UCLOUVAIN

        context['requested_documents'] = {
            document.identifiant: {
                'reason': self.proposition.documents_demandes.get(document.identifiant, {}).get('reason', ''),
                'label': document.libelle_langue_candidat,
            }
            for document in self.requestable_documents
        }

        context['candidate_language'] = self.admission.candidate.language

        return context

    def get_email_template(self):
        current_language = self.admission.candidate.language
        current_date = datetime.date.today()

        email_template_identifier = (
            {
                CONTEXT_GENERAL: ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_GENERAL,
                CONTEXT_DOCTORATE: ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_DOCTORATE,
                CONTEXT_CONTINUING: ADMISSION_EMAIL_REQUEST_FAC_DOCUMENTS_CONTINUING,
            }
            if ProgramManager.belong_to(self.request.user.person)
            else {
                CONTEXT_GENERAL: ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_GENERAL,
                CONTEXT_DOCTORATE: ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_DOCTORATE,
                CONTEXT_CONTINUING: ADMISSION_EMAIL_REQUEST_SIC_DOCUMENTS_CONTINUING,
            }
        )[self.current_context]

        mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
            email_template_identifier,
            current_language,
        )

        formation = self.proposition.doctorat if self.is_doctorate else self.proposition.formation

        management_entity = (
            EntityVersion.objects.filter(
                acronym=formation.sigle_entite_gestion,
                start_date__lte=current_date,
            )
            .exclude(end_date__lte=current_date)
            .values('title')
            .first()
        )

        tokens = {
            'admission_reference': self.proposition.reference,
            'training_campus': formation.campus,
            'training_title': getattr(
                self.admission.training,
                'title' if current_language == settings.LANGUAGE_CODE_FR else 'title_english',
            ),
            'training_acronym': formation.sigle,
            'training_year': format_academic_year(self.proposition.annee_calculee),
            'admission_link_front': settings.ADMISSION_FRONTEND_LINK.format(
                context=self.current_context,
                uuid=self.proposition.uuid,
            ),
            'request_deadline': f'<span id="request_deadline">_</span>',  # Will be updated through JS
            'management_entity_name': management_entity.get('title') if management_entity else '',
            'management_entity_acronym': formation.sigle_entite_gestion,
            'requested_documents': '<ul id="requested-documents-email-list"></ul>',  # Will be updated through JS
        }

        return mail_template.render_subject(tokens=tokens), mail_template.body_as_html(tokens=tokens)

    def form_valid(self, form):
        message_bus_instance.invoke(
            ReclamerDocumentsAuCandidatParFACCommand(
                uuid_demande=self.admission_uuid,
                identifiants_documents=form.cleaned_data['documents'],
                auteur=self.request.user.username,
                a_echeance_le=form.cleaned_data['deadline'],
                objet_message=form.cleaned_data['message_object'],
                corps_message=form.cleaned_data['message_content'],
            ) if self.is_fac else ReclamerDocumentsAuCandidatParSICCommand(
                uuid_demande=self.admission_uuid,
                identifiants_documents=form.cleaned_data['documents'],
                auteur=self.request.user.username,
                a_echeance_le=form.cleaned_data['deadline'],
                objet_message=form.cleaned_data['message_object'],
                corps_message=form.cleaned_data['message_content'],
            )
        )
        self.message_on_success = _('The documents have been requested to the candidate')
        return super().form_valid(self.get_form())


class BaseUploadFreeCandidateDocumentView(AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    form_class = UploadFreeDocumentForm
    permission_required = 'admission.view_documents_management'
    template_name = 'admission/document/upload_free_document.html'
    htmx_template_name = 'admission/document/upload_free_document.html'

    @property
    def document_type(self) -> str:
        raise NotImplementedError

    def form_valid(self, form) -> HttpResponse:
        message_bus_instance.invoke(
            DeposerDocumentLibreParGestionnaireCommand(
                uuid_demande=self.kwargs.get('uuid'),
                auteur=self.request.user.username,
                token_document=form.cleaned_data['file'][0],
                type_document=self.document_type,
                nom_document=form.cleaned_data['file_name'],
            ),
        )
        return super().form_valid(self.form_class())


class UploadFreeCandidateDocumentView(BaseUploadFreeCandidateDocumentView):
    urlpatterns = 'free-candidate-upload'

    @property
    def document_type(self):
        return (
            TypeDocument.CANDIDAT_FAC.name
            if ProgramManager.belong_to(self.request.user.person)
            else TypeDocument.CANDIDAT_SIC.name
        )


class UploadFreeInternalDocumentView(BaseUploadFreeCandidateDocumentView):
    urlpatterns = 'free-internal-upload'

    @property
    def document_type(self):
        return (
            TypeDocument.INTERNE_FAC.name
            if ProgramManager.belong_to(self.request.user.person)
            else TypeDocument.INTERNE_SIC.name
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
        return super().form_valid(self.form_class())


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
