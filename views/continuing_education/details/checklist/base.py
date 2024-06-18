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

from typing import Dict, Set, List

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from osis_comment.models import CommentEntry
from osis_mail_template.exceptions import EmptyMailTemplateContent
from osis_mail_template.models import MailTemplate

from admission.auth.roles.program_manager import ProgramManager
from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import (
    ResumeEtEmplacementsDocumentsPropositionDTO,
)
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.enums.statut import STATUTS_TOUTE_PROPOSITION_SOUMISE_HORS_FRAIS_DOSSIER_OU_ANNULEE
from admission.ddd.admission.formation_continue.commands import (
    RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery,
    RecupererQuestionsSpecifiquesQuery,
)
from admission.ddd.admission.formation_continue.domain.model.enums import OngletsChecklist
from admission.exports.admission_recap.section import get_dynamic_questions_by_tab
from admission.forms import disable_unavailable_forms
from admission.forms.admission.checklist import (
    CommentForm,
)
from admission.forms.admission.continuing_education.checklist import (
    StudentReportForm,
    DecisionFacApprovalForm,
    DecisionCancelForm,
    DecisionValidationForm,
    DecisionDenyForm,
    DecisionHoldForm,
    CloseForm,
    SendToFacForm,
)
from admission.mail_templates import (
    ADMISSION_EMAIL_DECISION_FAC_APPROVAL_WITH_CONDITION,
    ADMISSION_EMAIL_DECISION_FAC_APPROVAL_WITHOUT_CONDITION,
    ADMISSION_EMAIL_DECISION_DENY,
    ADMISSION_EMAIL_DECISION_ON_HOLD,
    ADMISSION_EMAIL_DECISION_VALIDATION,
    ADMISSION_EMAIL_DECISION_CANCEL,
    ADMISSION_EMAIL_DECISION_IUFC_COMMENT_FOR_FAC,
)
from admission.utils import get_salutation_prefix, get_portal_admission_url, get_backoffice_admission_url
from admission.views.common.mixins import LoadDossierViewMixin
from infrastructure.messages_bus import message_bus_instance
from osis_role.templatetags.osis_role import has_perm

__namespace__ = False

__all__ = [
    'ChecklistView',
]


class CheckListDefaultContextMixin(LoadDossierViewMixin):
    extra_context = {
        'checklist_tabs': {checklist_tab.name: checklist_tab.value for checklist_tab in OngletsChecklist},
        'hide_files': True,
    }

    @cached_property
    def can_update_checklist_tab(self):
        return has_perm('admission.change_checklist', user=self.request.user, obj=self.admission)

    @cached_property
    def can_update_iufc_checklist_tab(self):
        return has_perm('admission.change_checklist_iufc', user=self.request.user, obj=self.admission)

    @cached_property
    def mail_tokens(self):
        candidate = self.admission.candidate
        person = self.request.user.person

        training_title = {
            settings.LANGUAGE_CODE_FR: self.proposition.formation.intitule_fr,
            settings.LANGUAGE_CODE_EN: self.proposition.formation.intitule,
        }[candidate.language]

        program_managers = ProgramManager.objects.filter(
            education_group=self.admission.training.education_group,
        ).select_related('person')

        managers_emails = (' ' + _('or') + ' ').join(
            f'<a href="mailto:{program_manager.person.email}">{program_manager.person.email}</a>'
            for program_manager in program_managers
        )

        return {
            'candidate_first_name': self.proposition.prenom_candidat,
            'candidate_last_name': self.proposition.nom_candidat,
            'greetings': get_salutation_prefix(self.admission.candidate),
            'application_reference': self.proposition.reference,
            'training_acronym': self.proposition.formation.sigle,
            'training_title': training_title,
            'application_link': get_portal_admission_url('continuing-education', self.admission_uuid),
            'managers_emails': managers_emails,
            'sender_name': f'{person.first_name} {person.last_name}',
        }

    @cached_property
    def decision_fac_approval_form(self):
        tokens = self.mail_tokens

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_DECISION_FAC_APPROVAL_WITH_CONDITION,
                self.admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''

        return DecisionFacApprovalForm(
            data=self.request.POST
            if self.request.method == 'POST' and 'decision-fac-approval-subject' in self.request.POST
            else None,
            prefix='decision-fac-approval',
            initial={
                'subject': subject,
            },
        )

    def get_decision_fac_approval_mail_bodies(self):
        bodies = {}
        tokens = self.mail_tokens
        tokens['conditions'] = '__CONDITION__'

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_DECISION_FAC_APPROVAL_WITH_CONDITION,
                self.admission.candidate.language,
            )
            bodies['decision_fac_approval_mail_body_with_condition'] = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            bodies['decision_fac_approval_mail_body_with_condition'] = ''

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_DECISION_FAC_APPROVAL_WITHOUT_CONDITION,
                self.admission.candidate.language,
            )
            bodies['decision_fac_approval_mail_body_without_condition'] = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            bodies['decision_fac_approval_mail_body_without_condition'] = ''

        return bodies

    @cached_property
    def decision_deny_form(self):
        tokens = self.mail_tokens
        tokens['reasons'] = '__MOTIF__'

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_DECISION_DENY,
                self.admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        return DecisionDenyForm(
            candidate_language=self.admission.candidate.language,
            data=self.request.POST
            if self.request.method == 'POST' and 'decision-deny-subject' in self.request.POST
            else None,
            prefix='decision-deny',
            initial={
                'subject': subject,
                'body': body,
            },
        )

    @cached_property
    def decision_hold_form(self):
        tokens = self.mail_tokens
        tokens['reasons'] = '__MOTIF__'

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_DECISION_ON_HOLD,
                self.admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        return DecisionHoldForm(
            candidate_language=self.admission.candidate.language,
            data=self.request.POST
            if self.request.method == 'POST' and 'decision-hold-subject' in self.request.POST
            else None,
            prefix='decision-hold',
            initial={
                'subject': subject,
                'body': body,
            },
        )

    @cached_property
    def decision_cancel_form(self):
        tokens = self.mail_tokens

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_DECISION_CANCEL,
                self.admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        return DecisionCancelForm(
            data=self.request.POST
            if self.request.method == 'POST' and 'decision-cancel-subject' in self.request.POST
            else None,
            prefix='decision-cancel',
            initial={
                'subject': subject,
                'body': body,
            },
        )

    @cached_property
    def decision_validation_form(self):
        tokens = self.mail_tokens

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_DECISION_VALIDATION,
                self.admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        return DecisionValidationForm(
            data=self.request.POST
            if self.request.method == 'POST' and 'decision-validation-subject' in self.request.POST
            else None,
            prefix='decision-validation',
            initial={
                'subject': subject,
                'body': body,
            },
        )

    @cached_property
    def decision_close_form(self):
        return CloseForm(
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='decision-close',
        )

    @cached_property
    def decision_send_to_fac_form(self):
        tokens = self.mail_tokens
        tokens['comment'] = '__COMMENT__'
        tokens['application_link'] = get_backoffice_admission_url('continuing-education', self.admission_uuid)

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_DECISION_IUFC_COMMENT_FOR_FAC,
                settings.LANGUAGE_CODE_FR,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        return SendToFacForm(
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='decision-send-to-fac',
            initial={
                'subject': subject,
                'body': body,
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        checklist_additional_icons = {}

        context['checklist_additional_icons'] = checklist_additional_icons
        context['can_update_checklist_tab'] = self.can_update_checklist_tab
        context['can_change_payment'] = self.request.user.has_perm('admission.change_payment', self.admission)
        context['can_change_faculty_decision'] = self.request.user.has_perm(
            'admission.checklist_change_faculty_decision',
            self.admission,
        )
        context['student_report_form'] = StudentReportForm(instance=self.admission)
        context['decision_fac_approval_form'] = self.decision_fac_approval_form
        context.update(self.get_decision_fac_approval_mail_bodies())
        context['decision_hold_form'] = self.decision_hold_form
        context['decision_deny_form'] = self.decision_deny_form
        context['decision_cancel_form'] = self.decision_cancel_form
        context['decision_validation_form'] = self.decision_validation_form
        context['decision_close_form'] = self.decision_close_form
        context['decision_send_to_fac_form'] = self.decision_send_to_fac_form

        # Initialize comments forms
        tab_names = [
            'fiche_etudiant',
            'decision__IUFC_for_FAC',
            'decision__FAC_for_IUFC',
        ]

        comments = {
            ('__'.join(c.tags)): c
            for c in CommentEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__overlap=OngletsChecklist.get_names(),
            )
        }

        context['comment_forms'] = {
            tab_name: CommentForm(
                comment=comments.get(tab_name, None),
                form_url=resolve_url(f'{self.base_namespace}:save-comment', uuid=self.admission_uuid, tab=tab_name),
                prefix=tab_name,
            )
            for tab_name in tab_names
        }

        disable_unavailable_forms(
            forms_by_access={
                context['student_report_form']: self.can_update_checklist_tab,
                context['decision_fac_approval_form']: self.can_update_checklist_tab,
                context['decision_hold_form']: self.can_update_checklist_tab,
                context['decision_deny_form']: self.can_update_checklist_tab,
                context['decision_cancel_form']: self.can_update_checklist_tab,
                context['decision_validation_form']: self.can_update_iufc_checklist_tab,
                context['decision_close_form']: self.can_update_checklist_tab,
                context['decision_send_to_fac_form']: self.can_update_iufc_checklist_tab,
                **{
                    comment_form: self.request.user.has_perm(comment_form.permission, self.admission)
                    for comment_form in context['comment_forms'].values()
                },
            }
        )

        context['autres_demandes'] = [
            demande
            for demande in message_bus_instance.invoke(
                ListerToutesDemandesQuery(
                    annee_academique=self.admission.determined_academic_year.year,
                    matricule_candidat=self.admission.candidate.global_id,
                    etats=STATUTS_TOUTE_PROPOSITION_SOUMISE_HORS_FRAIS_DOSSIER_OU_ANNULEE,
                )
            )
            if demande.uuid != self.admission_uuid
        ]

        return context


class ChecklistView(
    CheckListDefaultContextMixin,
    TemplateView,
):
    urlpatterns = 'checklist'
    template_name = "admission/continuing_education/checklist.html"
    permission_required = 'admission.view_checklist'

    @classmethod
    def checklist_documents_by_tab(cls, specific_questions: List[QuestionSpecifiqueDTO]) -> Dict[str, Set[str]]:
        documents_by_tab = {
            'fiche_etudiant': {
                'CARTE_IDENTITE',
                'PASSEPORT',
                'COPIE_TITRE_SEJOUR',
                'DOSSIER_ANALYSE',
            },
            'decision': {
                'CARTE_IDENTITE',
                'PASSEPORT',
                'COPIE_TITRE_SEJOUR',
                'DOSSIER_ANALYSE',
            },
        }
        return documents_by_tab

    def get_template_names(self):
        if self.request.htmx:
            return ["admission/continuing_education/checklist_menu.html"]
        return ["admission/continuing_education/checklist.html"]

    def get_context_data(self, **kwargs):
        from infrastructure.messages_bus import message_bus_instance

        context = super().get_context_data(**kwargs)
        if not self.request.htmx:
            # Retrieve data related to the proposition
            command_result: ResumeEtEmplacementsDocumentsPropositionDTO = message_bus_instance.invoke(
                RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery(uuid_proposition=self.admission_uuid),
            )

            context['resume_proposition'] = command_result.resume

            specific_questions: List[QuestionSpecifiqueDTO] = message_bus_instance.invoke(
                RecupererQuestionsSpecifiquesQuery(
                    uuid_proposition=self.admission_uuid,
                    onglets=[
                        Onglets.INFORMATIONS_ADDITIONNELLES.name,
                        Onglets.ETUDES_SECONDAIRES.name,
                        Onglets.CURRICULUM.name,
                    ],
                )
            )

            context['specific_questions_by_tab'] = get_dynamic_questions_by_tab(specific_questions)

            # Documents
            admission_documents = command_result.emplacements_documents

            documents_by_tab = self.checklist_documents_by_tab(specific_questions=specific_questions)

            context['documents'] = {
                tab_name: sorted(
                    [
                        admission_document
                        for admission_document in admission_documents
                        if admission_document.identifiant.split('.')[-1] in tab_documents
                    ],
                    key=lambda doc: doc.libelle,
                )
                for tab_name, tab_documents in documents_by_tab.items()
            }

        return context
