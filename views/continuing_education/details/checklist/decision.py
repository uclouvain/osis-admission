# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.forms import Form
from django.http import HttpResponseForbidden
from django.views.generic import FormView, TemplateView
from osis_history.utilities import add_history_entry
from osis_mail_template.utils import transform_html_to_text
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from admission.auth.roles.program_manager import ProgramManager
from admission.ddd.admission.formation_continue.commands import (
    AnnulerPropositionCommand,
    AnnulerReclamationDocumentsAuCandidatCommand,
    ApprouverParFacCommand,
    CloturerPropositionCommand,
    MettreAValiderCommand,
    MettreEnAttenteCommand,
    RefuserPropositionCommand,
    ValiderPropositionCommand,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    STATUTS_PROPOSITION_CONTINUE_SOUMISE_POUR_CANDIDAT,
    ChoixStatutChecklist,
    ChoixStatutPropositionContinue,
)
from admission.forms.admission.continuing_education.checklist import (
    CloseForm,
    DecisionCancelForm,
    DecisionDenyForm,
    DecisionFacApprovalForm,
    DecisionHoldForm,
    DecisionValidationForm,
    SendToFacForm,
)
from admission.infrastructure.utils import get_message_to_historize
from admission.views.common.detail_tabs.checklist import change_admission_status
from admission.views.common.mixins import AdmissionFormMixin
from admission.views.continuing_education.details.checklist.base import (
    CheckListDefaultContextMixin,
)
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException

__namespace__ = False

__all__ = [
    'FacApprovalFormView',
    'HoldFormView',
    'DenyFormView',
    'CancelFormView',
    'ValidationFormView',
    'CloseFormView',
    'DecisionChangeStatusToBeProcessedView',
    'DecisionChangeStatusTakenInChargeView',
    'SendToFacFormView',
    'ToValidateFormView',
]


class FacApprovalFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'decision-fac-approval'
    urlpatterns = 'decision-fac-approval'
    template_name = 'admission/continuing_education/includes/checklist/decision_fac_approval_form.html'
    htmx_template_name = 'admission/continuing_education/includes/checklist/decision_fac_approval_form.html'
    permission_required = 'admission.change_checklist'
    form_class = DecisionFacApprovalForm

    def get_form(self, form_class=None):
        return self.decision_fac_approval_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ApprouverParFacCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    objet_message=form.cleaned_data['subject'],
                    corps_message=form.cleaned_data['body'],
                    condition=form.cleaned_data.get('condition_acceptation', ''),
                )
            )
        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)


class HoldFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'decision-hold'
    urlpatterns = 'decision-hold'
    template_name = 'admission/continuing_education/includes/checklist/decision_hold_form.html'
    htmx_template_name = 'admission/continuing_education/includes/checklist/decision_hold_form.html'
    permission_required = 'admission.change_checklist'
    form_class = DecisionHoldForm

    def get_form(self, form_class=None):
        return self.decision_hold_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                MettreEnAttenteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    objet_message=form.cleaned_data['subject'],
                    corps_message=form.cleaned_data['body'],
                    motif=form.cleaned_data['reason'],
                    autre_motif=form.cleaned_data.get('other_reason', ''),
                )
            )
        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)


class ToValidateFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'decision-to-validate'
    urlpatterns = 'decision-to-validate'
    template_name = 'admission/empty_template.html'
    htmx_template_name = 'admission/empty_template.html'
    permission_required = 'admission.change_checklist_iufc'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                MettreAValiderCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)


class DenyFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'decision-deny'
    urlpatterns = 'decision-deny'
    template_name = 'admission/continuing_education/includes/checklist/decision_deny_form.html'
    htmx_template_name = 'admission/continuing_education/includes/checklist/decision_deny_form.html'
    permission_required = 'admission.change_checklist'
    form_class = DecisionDenyForm

    def get_form(self, form_class=None):
        return self.decision_deny_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                RefuserPropositionCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    objet_message=form.cleaned_data['subject'],
                    corps_message=form.cleaned_data['body'],
                    motif=form.cleaned_data['reason'],
                    autre_motif=form.cleaned_data.get('other_reason', ''),
                )
            )
        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)


class CancelFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'decision-cancel'
    urlpatterns = 'decision-cancel'
    template_name = 'admission/continuing_education/includes/checklist/decision_cancel_form.html'
    htmx_template_name = 'admission/continuing_education/includes/checklist/decision_cancel_form.html'
    permission_required = 'admission.change_checklist'
    form_class = DecisionCancelForm

    def get_form(self, form_class=None):
        return self.decision_cancel_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                AnnulerPropositionCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    objet_message=form.cleaned_data['subject'],
                    corps_message=form.cleaned_data['body'],
                    motif=form.cleaned_data['reason'],
                )
            )
        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)


class ValidationFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'decision-validation'
    urlpatterns = 'decision-validation'
    template_name = 'admission/empty_template.html'
    htmx_template_name = 'admission/empty_template.html'
    permission_required = 'admission.change_checklist_iufc'
    form_class = Form

    def dispatch(self, request, *args, **kwargs):
        if self.admission.is_in_quarantine:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ValiderPropositionCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)


class CloseFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'decision-close'
    urlpatterns = 'decision-close'
    template_name = 'admission/continuing_education/includes/checklist/decision_close_form.html'
    htmx_template_name = 'admission/continuing_education/includes/checklist/decision_close_form.html'
    permission_required = 'admission.change_checklist'
    form_class = CloseForm

    def get_form(self, form_class=None):
        return self.decision_close_form

    def form_valid(self, form):
        try:
            if self.admission.status in STATUTS_PROPOSITION_CONTINUE_SOUMISE_POUR_CANDIDAT:
                message_bus_instance.invoke(
                    AnnulerReclamationDocumentsAuCandidatCommand(
                        uuid_proposition=self.admission_uuid,
                        auteur=self.request.user.person.global_id,
                    )
                )
            message_bus_instance.invoke(
                CloturerPropositionCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)


class DecisionChangeStatusToBeProcessedView(CheckListDefaultContextMixin, HtmxPermissionRequiredMixin, TemplateView):
    urlpatterns = 'decision-change-status-to-be-processed'
    template_name = 'admission/continuing_education/includes/checklist/decision_to_be_processed_form.html'
    permission_required = 'admission.change_checklist'

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()

        change_admission_status(
            tab='decision',
            admission_status=admission.checklist['initial']['decision']['statut'],
            extra={},
            replace_extra=True,
            admission=admission,
            global_status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            author=self.request.user.person,
        )

        response = self.render_to_response(self.get_context_data())
        response.headers['HX-Refresh'] = 'true'

        add_history_entry(
            admission.uuid,
            'Le statut de la proposition a évolué au cours du processus de décision : Demande confirmée (À traiter).',
            'The status of the proposal has changed during the decision process: Application confirmed '
            '(To be processed).',
            '{first_name} {last_name}'.format(
                first_name=self.request.user.person.first_name,
                last_name=self.request.user.person.last_name,
            ),
            tags=['proposition', 'decision', 'status-changed'],
        )
        return response


class DecisionChangeStatusTakenInChargeView(CheckListDefaultContextMixin, HtmxPermissionRequiredMixin, TemplateView):
    urlpatterns = 'decision-change-status-taken-in-charge'
    template_name = 'admission/continuing_education/includes/checklist/decision_taken_in_charge_form.html'
    permission_required = 'admission.change_checklist'

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()

        change_admission_status(
            tab='decision',
            admission_status=ChoixStatutChecklist.GEST_EN_COURS.name,
            extra={'en_cours': 'taken_in_charge'},
            replace_extra=True,
            admission=admission,
            global_status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            author=self.request.user.person,
        )

        response = self.render_to_response(self.get_context_data())
        response.headers['HX-Refresh'] = 'true'

        add_history_entry(
            admission.uuid,
            'Le statut de la proposition a évolué au cours du processus de décision : Demande confirmée '
            '(Pris en charge).',
            'The status of the proposal has changed during the decision process: Application confirmed '
            '(Taken in charge).',
            '{first_name} {last_name}'.format(
                first_name=self.request.user.person.first_name,
                last_name=self.request.user.person.last_name,
            ),
            tags=['proposition', 'decision', 'status-changed'],
        )
        return response


class SendToFacFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'decision-send-to-fac'
    urlpatterns = 'decision-send-to-fac'
    template_name = 'admission/continuing_education/includes/checklist/decision_send_to_fac_form.html'
    htmx_template_name = 'admission/continuing_education/includes/checklist/decision_send_to_fac_form.html'
    permission_required = 'admission.change_checklist_iufc'
    form_class = SendToFacForm

    def get_form(self, form_class=None):
        return self.decision_send_to_fac_form

    def form_valid(self, form):
        subject = form.cleaned_data['subject']
        body = form.cleaned_data['body']

        recipients_managers = ProgramManager.objects.filter(
            education_group=self.admission.training.education_group,
        ).select_related('person')

        for manager in recipients_managers:
            email_notification = EmailNotification(
                recipient=manager.person.email,
                subject=subject,
                html_content=body,
                plain_text_content=transform_html_to_text(body),
            )

            email_message = EmailNotificationHandler.build(email_notification)
            EmailNotificationHandler.create(email_message, person=manager.person)

            message_a_historiser = get_message_to_historize(email_message)

            add_history_entry(
                self.admission_uuid,
                message_a_historiser[settings.LANGUAGE_CODE_FR],
                message_a_historiser[settings.LANGUAGE_CODE_EN],
                f'{self.request.user.person.first_name} {self.request.user.person.last_name}',
                tags=['proposition', 'email-to-fac', 'message'],
            )

        return super().form_valid(form)
