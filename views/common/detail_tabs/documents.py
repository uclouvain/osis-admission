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
from typing import List

from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import FormView
from osis_mail_template.models import MailTemplate

from admission.auth.roles.program_manager import ProgramManager
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import (
    StatutEmplacementDocument,
    EMPLACEMENTS_DOCUMENTS_INTERNES,
    EMPLACEMENTS_FAC,
    EMPLACEMENTS_SIC,
)
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.forms.admission.document import (
    RequestAllDocumentsForm,
)
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

__all__ = [
    'DocumentView',
]


class DocumentView(LoadDossierViewMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    template_name = 'admission/document/base.html'
    permission_required = 'admission.view_documents_management'
    urlpatterns = 'documents'
    form_class = RequestAllDocumentsForm
    name = 'document-list'

    retrieve_documents_command = {
        CONTEXT_GENERAL: general_education_commands.RecupererDocumentsPropositionQuery,
    }
    fac_documents_request_command = {
        CONTEXT_GENERAL: general_education_commands.ReclamerDocumentsAuCandidatParFACCommand,
    }
    sic_documents_request_command = {
        CONTEXT_GENERAL: general_education_commands.ReclamerDocumentsAuCandidatParSICCommand,
    }

    def get_template_names(self):
        self.htmx_template_name = (
            'admission/document/request_all_documents.html'
            if self.request.method == 'POST'
            else 'admission/document/base_htmx.html'
        )
        return super().get_template_names()

    @cached_property
    def is_fac(self):
        return ProgramManager.belong_to(self.request.user.person)

    @cached_property
    def deadline(self):
        return datetime.date.today() + datetime.timedelta(days=15)

    @cached_property
    def documents(self) -> List[EmplacementDocumentDTO]:
        return (
            message_bus_instance.invoke(
                self.retrieve_documents_command[self.current_context](
                    uuid_proposition=self.admission_uuid,
                )
            )
            if self.current_context in self.retrieve_documents_command
            else []
        )

    @cached_property
    def requestable_documents(self):
        requestable_types = EMPLACEMENTS_FAC if self.is_fac else EMPLACEMENTS_SIC
        return [
            document
            for document in self.documents
            if document.statut == StatutEmplacementDocument.A_RECLAMER.name and document.type in requestable_types
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
        context['EMPLACEMENTS_DOCUMENTS_INTERNES'] = EMPLACEMENTS_DOCUMENTS_INTERNES
        context['EMPLACEMENTS_FAC'] = EMPLACEMENTS_FAC
        context['next'] = self.request.GET.get('next')

        context['requested_documents'] = {
            document.identifiant: {
                'reason': self.proposition.documents_demandes.get(document.identifiant, {}).get('reason', ''),
                'label': document.libelle_langue_candidat,
                'tab_label': document.nom_onglet,
                'candidate_language_tab_label': document.nom_onglet_langue_candidat,
                'tab': document.onglet,
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
        request_command = (self.fac_documents_request_command if self.is_fac else self.sic_documents_request_command)[
            self.current_context
        ]
        message_bus_instance.invoke(
            request_command(
                uuid_proposition=self.admission_uuid,
                identifiants_emplacements=form.cleaned_data['documents'],
                auteur=self.request.user.person.global_id,
                a_echeance_le=form.cleaned_data['deadline'],
                objet_message=form.cleaned_data['message_object'],
                corps_message=form.cleaned_data['message_content'],
            )
        )
        self.message_on_success = _('The documents have been requested to the candidate')
        self.htmx_trigger_form_extra['refresh_details'] = 'reset'
        self.htmx_trigger_form_extra['refresh_list'] = True

        return super().form_valid(self.get_form())
