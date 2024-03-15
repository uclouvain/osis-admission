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
import datetime
from typing import List

from django.conf import settings
from django.forms import forms
from django.shortcuts import resolve_url
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
    STATUTS_EMPLACEMENT_DOCUMENT_A_RECLAMER,
)
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
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
from admission.utils import (
    format_academic_year,
    get_portal_admission_list_url,
    get_backoffice_admission_url,
    get_portal_admission_url,
    get_salutation_prefix,
)
from admission.views.doctorate.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.models.entity_version import EntityVersion
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin

__all__ = [
    'CancelDocumentRequestView',
    'DocumentView',
]

__namespace__ = False


class CancelDocumentRequestView(
    LoadDossierViewMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    HtmxMixin,
    FormView,
):
    form_class = forms.Form
    permission_required = 'admission.cancel_document_request'
    urlpatterns = 'cancel-document-request'
    name = 'cancel-document-request'
    template_name = 'admission/no_document.html'
    htmx_template_name = 'admission/no_document.html'
    default_htmx_trigger_form_extra = {
        'refresh_details': 'reset',
        'refresh_list': True,
    }
    message_on_success = _('The documents request have been cancelled')

    def form_valid(self, form):
        message_bus_instance.invoke(
            general_education_commands.AnnulerReclamationDocumentsAuCandidatCommand(
                uuid_proposition=self.admission_uuid,
                auteur=self.request.user.person.global_id,
                par_fac=self.is_fac,
            )
        )
        return super().form_valid(form)

    def get_success_url(self):
        return resolve_url(f'{self.base_namespace}:documents', uuid=self.admission_uuid)


class DocumentView(LoadDossierViewMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, HtmxMixin, FormView):
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

    def get_permission_required(self):
        self.permission_required = (
            'admission.change_documents_management'
            if self.request.method == 'POST'
            else 'admission.view_documents_management'
        )
        return super().get_permission_required()

    def get_template_names(self):
        self.htmx_template_name = (
            'admission/document/request_all_documents.html'
            if self.request.method == 'POST'
            else 'admission/document/base_htmx.html'
        )
        if self.admission.status == ChoixStatutPropositionGenerale.EN_BROUILLON.name:
            self.template_name = 'admission/document/base_in_progress.html'
        else:
            self.template_name = 'admission/document/base.html'
        return super().get_template_names()

    @cached_property
    def deadline(self):
        today_date = datetime.date.today()

        if today_date.month == 9 and today_date.day >= 15:
            # If date between the 15/09 and the 30/09 -> return 30/09
            return datetime.date(today_date.year, today_date.month, 30)
        else:
            # Otherwise return today + 15 days
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
            if document.statut in STATUTS_EMPLACEMENT_DOCUMENT_A_RECLAMER and document.type in requestable_types
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
        kwargs['proposition_uuid'] = self.admission_uuid
        kwargs['only_limited_request_choices'] = self.is_fac
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['documents'] = self.documents
        context['EMPLACEMENTS_DOCUMENTS_INTERNES'] = EMPLACEMENTS_DOCUMENTS_INTERNES
        context['EMPLACEMENTS_FAC'] = EMPLACEMENTS_FAC
        context['STATUTS_EMPLACEMENT_DOCUMENT_A_RECLAMER'] = STATUTS_EMPLACEMENT_DOCUMENT_A_RECLAMER
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
            'training_acronym': formation.sigle,
            'training_year': format_academic_year(self.proposition.annee_calculee),
            'request_deadline': f'<span class="request_deadline">_</span>',  # Will be updated through JS
            'management_entity_name': management_entity.get('title') if management_entity else '',
            'management_entity_acronym': formation.sigle_entite_gestion,
            'requested_documents': '<ul id="immediate-requested-documents-email-list"></ul>',
            'later_requested_documents': '<ul id="later-requested-documents-email-list"></ul>',
            'candidate_first_name': self.proposition.prenom_candidat,
            'candidate_last_name': self.proposition.nom_candidat,
            'training_title': {
                settings.LANGUAGE_CODE_FR: self.admission.training.title,
                settings.LANGUAGE_CODE_EN: self.admission.training.title_english,
            }[self.proposition.langue_contact_candidat],
            'admissions_link_front': get_portal_admission_list_url(),
            'admission_link_front': get_portal_admission_url('general-education', self.admission_uuid),
            'admission_link_back': get_backoffice_admission_url('general-education', self.admission_uuid),
            'salutation': get_salutation_prefix(self.admission.candidate),
        }

        return mail_template.render_subject(tokens=tokens), mail_template.body_as_html(tokens=tokens)

    def form_valid(self, form):
        request_command = (self.fac_documents_request_command if self.is_fac else self.sic_documents_request_command)[
            self.current_context
        ]
        message_bus_instance.invoke(
            request_command(
                uuid_proposition=self.admission_uuid,
                identifiants_emplacements=form.cleaned_data['requested_documents'],
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
