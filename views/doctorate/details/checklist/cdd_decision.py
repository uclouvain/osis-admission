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
from django.forms import Form
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from osis_history.models import HistoryEntry

from admission.ddd.admission.doctorat.preparation.commands import (
    ApprouverPropositionParCddCommand,
    CloturerPropositionParCddCommand,
    EnvoyerPropositionACddLorsDeLaDecisionCddCommand,
    EnvoyerPropositionAuSicLorsDeLaDecisionCddCommand,
    PasserEtatACompleterParSicDecisionCddCommand,
    PasserEtatATraiterDecisionCddCommand,
    PasserEtatPrisEnChargeDecisionCddCommand,
    RefuserPropositionParCddCommand,
    SpecifierInformationsAcceptationPropositionParCddCommand,
    SpecifierMotifsRefusPropositionParCDDCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_CDD_POUR_DECISION,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD_ETENDUS,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC_ETENDUS,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
)
from admission.ddd.admission.doctorat.preparation.dtos import PromoteurDTO
from admission.ddd.admission.shared_kernel.enums.type_demande import TypeDemande
from admission.forms.admission.checklist import (
    DoctorateCddDecisionApprovalForm,
    DoctorateFacDecisionRefusalForm,
    SendEMailForm,
)
from admission.mail_templates import (
    ADMISSION_EMAIL_CDD_APPROVAL_DOCTORATE_WITH_BELGIAN_DIPLOMA,
    ADMISSION_EMAIL_CDD_APPROVAL_DOCTORATE_WITHOUT_BELGIAN_DIPLOMA,
)
from admission.utils import (
    get_access_titles_names,
    get_salutation_prefix,
)
from admission.views.common.mixins import AdmissionFormMixin
from admission.views.doctorate.details.checklist.mixins import (
    CheckListDefaultContextMixin,
    get_email,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'CddDecisionSendToCddView',
    'CddRefusalDecisionView',
    'CddApprovalDecisionView',
    'CddDecisionSendToSicView',
    'CddApprovalFinalDecisionView',
    'CddDecisionClosedView',
    'CddDecisionToProcessedView',
    'CddDecisionTakenInChargeView',
    'CddDecisionToCompleteBySicView',
]


__namespace__ = False


# CDD decision
class CddDecisionMixin(CheckListDefaultContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['in_sic_statuses'] = self.admission.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC_ETENDUS
        context['in_cdd_statuses'] = self.admission.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD_ETENDUS
        context['sic_statuses_for_transfer'] = ChoixStatutPropositionDoctorale.get_specific_values(
            STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_CDD_POUR_DECISION
        )
        context['cdd_statuses_for_transfer'] = ChoixStatutPropositionDoctorale.get_specific_values(
            STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD
        )
        context['is_sic'] = self.is_sic
        context['fac_decision_refusal_form'] = self.cdd_decision_refusal_form

        context.setdefault('history_entries', {})

        cdd_decision_history = (
            HistoryEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__contains=['proposition', 'cdd-decision', 'message'],
            )
            .order_by('-created')
            .first()
        )

        context['history_entries']['cdd_decision'] = cdd_decision_history

        context['cdd_decision_refusal_form'] = self.cdd_decision_refusal_form

        can_change_decision = self.request.user.has_perm('admission.checklist_change_faculty_decision', self.admission)
        in_cdd_decision_closed_status = self.in_cdd_decision_closed_status()

        cdd_decision_to_processed_status_tooltip = ''
        cdd_decision_statuses_tooltip = ''

        if self.admission.status == ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name:
            cdd_decision_to_processed_status_tooltip = cdd_decision_statuses_tooltip = _(
                'Documents requested by the CDD are still expected from the candidate.'
            )
        elif can_change_decision and in_cdd_decision_closed_status:
            cdd_decision_statuses_tooltip = _('It is not possible to go from the "Closed" status to this status.')

        context['cdd_decision_to_processed_status_tooltip'] = cdd_decision_to_processed_status_tooltip
        context['cdd_decision_statuses_tooltip'] = cdd_decision_statuses_tooltip
        context['cdd_decision_to_processed_status_disabled'] = not can_change_decision
        context['cdd_decision_statuses_disabled'] = not can_change_decision or self.in_cdd_decision_closed_status()

        return context

    def in_cdd_decision_closed_status(self):
        current_cdd_checklist = self.admission.checklist.get('current', {}).get(OngletsChecklist.decision_cdd.name, {})
        closed_status = ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.decision_cdd.name]['CLOTURE']
        return closed_status.matches_dict(current_cdd_checklist)

    @cached_property
    def selected_access_titles_names(self):
        return get_access_titles_names(access_titles=self.selected_access_titles)

    @cached_property
    def cdd_decision_refusal_form(self):
        form_kwargs = {
            'prefix': 'cdd-decision-refusal',
        }

        if self.request.method == 'GET':
            form_kwargs['initial'] = {'reasons': self.admission_refusal_reasons}

        else:
            form_kwargs['data'] = self.request.POST

        return DoctorateFacDecisionRefusalForm(**form_kwargs)

    @cached_property
    def cdd_decision_approval_final_form(self):
        form_kwargs = {
            'prefix': 'cdd-decision-approval-final',
        }

        if self.request.method == 'GET':
            prerequisite_courses_list = render_to_string(
                'admission/includes/prerequisite_courses.html',
                context={'admission': self.proposition},
            )
            prerequisite_courses_communication = render_to_string(
                'admission/includes/prerequisite_courses_communication.html',
                context={'admission': self.proposition},
            )

            # Load the email template
            subject, body = get_email(
                template_identifier=(
                    ADMISSION_EMAIL_CDD_APPROVAL_DOCTORATE_WITH_BELGIAN_DIPLOMA
                    if self.proposition_resume.resume.curriculum.a_diplome_belge
                    else ADMISSION_EMAIL_CDD_APPROVAL_DOCTORATE_WITHOUT_BELGIAN_DIPLOMA
                ),
                language=self.proposition.langue_contact_candidat,
                proposition_dto=self.proposition,
                extra_tokens={
                    'greetings': get_salutation_prefix(self.admission.candidate),
                    'doctoral_commission': self.proposition.doctorat.intitule_entite_gestion,
                    'sender_name': f'{self.request.user.person.first_name} {self.request.user.person.last_name}',
                    'management_entity_acronym': self.proposition.doctorat.sigle_entite_gestion,
                    'program_managers_names': self.admission_program_managers_names,
                    'prerequisite_courses_list': prerequisite_courses_list,
                    'prerequisite_courses_communication': prerequisite_courses_communication,
                },
            )

            form_kwargs['initial'] = {
                'subject': subject,
                'body': body,
            }

        else:
            form_kwargs['data'] = self.request.POST

        return SendEMailForm(**form_kwargs)

    @cached_property
    def cdd_decision_approval_form(self):
        initial = {}

        if (
            self.request.method == 'GET'
            and self.proposition_resume.resume.groupe_supervision
            and self.proposition_resume.resume.groupe_supervision.promoteur_reference_dto
        ):
            reference_promoter: PromoteurDTO = self.proposition_resume.resume.groupe_supervision.promoteur_reference_dto

            initial['annual_program_contact_person_name'] = f'{reference_promoter.prenom} {reference_promoter.nom}'
            initial['annual_program_contact_person_email'] = reference_promoter.email

        return DoctorateCddDecisionApprovalForm(
            academic_year=self.admission.determined_academic_year.year,
            instance=self.admission if self.request.method != 'POST' else None,
            initial=initial,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='cdd-decision-approval',
            is_admission=self.admission.type_demande == TypeDemande.ADMISSION.name,
        )


class CddDecisionSendToCddView(
    AdmissionFormMixin,
    CddDecisionMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'cdd-decision-send-to-cdd'
    urlpatterns = {'cdd-decision-send-to-cdd': 'cdd-decision/send-to-cdd'}
    permission_required = 'admission.checklist_faculty_decision_transfer_to_fac'
    template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                EnvoyerPropositionACddLorsDeLaDecisionCddCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)
        self.htmx_refresh = True
        return super().form_valid(form)


class CddDecisionSendToSicView(
    AdmissionFormMixin,
    CddDecisionMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'cdd-decision-send-to-sic'
    urlpatterns = {'cdd-decision-send-to-sic': 'cdd-decision/send-to-sic'}
    template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    form_class = Form
    permission_required = 'admission.checklist_faculty_decision_transfer_to_sic_without_decision'

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                RefuserPropositionParCddCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
                if self.request.GET.get('refusal') and self.is_fac
                else EnvoyerPropositionAuSicLorsDeLaDecisionCddCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    envoi_par_cdd=self.is_fac,
                )
            )

        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        self.htmx_refresh = True

        return super().form_valid(form)


class CddRefusalDecisionView(
    CddDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'cdd-decision-refusal'
    urlpatterns = {'cdd-decision-refusal': 'cdd-decision/cdd-decision-refusal'}
    template_name = 'admission/doctorate/includes/checklist/cdd_decision_refusal_form.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/cdd_decision_refusal_form.html'

    def get_permission_required(self):
        return (
            (
                'admission.checklist_faculty_decision_transfer_to_sic_with_decision'
                if 'save_transfer' in self.request.POST
                else 'admission.checklist_change_faculty_decision'
            ),
        )

    def get_form(self, form_class=None):
        return self.cdd_decision_refusal_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierMotifsRefusPropositionParCDDCommand(
                    uuid_proposition=self.admission_uuid,
                    uuids_motifs=form.cleaned_data['reasons'],
                    autres_motifs=form.cleaned_data['other_reasons'],
                    gestionnaire=self.request.user.person.global_id,
                )
            )
            if 'save-transfer' in self.request.POST:
                message_bus_instance.invoke(
                    RefuserPropositionParCddCommand(
                        uuid_proposition=self.admission_uuid,
                        gestionnaire=self.request.user.person.global_id,
                    )
                )
                self.htmx_refresh = True
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class CddApprovalDecisionView(
    CddDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'cdd-decision-approval'
    urlpatterns = {'cdd-decision-approval': 'cdd-decision/cdd-decision-approval'}
    template_name = 'admission/doctorate/includes/checklist/cdd_decision_approval_form.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/cdd_decision_approval_form.html'
    permission_required = 'admission.checklist_change_faculty_decision'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['cdd_decision_approval_form'] = self.cdd_decision_approval_form
        context['selected_access_titles_names'] = self.selected_access_titles_names
        return context

    def get_form(self, form_class=None):
        return self.cdd_decision_approval_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierInformationsAcceptationPropositionParCddCommand(
                    uuid_proposition=self.admission_uuid,
                    avec_complements_formation=form.cleaned_data['with_prerequisite_courses'],
                    uuids_complements_formation=form.cleaned_data['prerequisite_courses'],
                    commentaire_complements_formation=form.cleaned_data['prerequisite_courses_fac_comment'],
                    nom_personne_contact_programme_annuel=form.cleaned_data['annual_program_contact_person_name'],
                    email_personne_contact_programme_annuel=form.cleaned_data['annual_program_contact_person_email'],
                    commentaire_programme_conjoint=form.cleaned_data['join_program_fac_comment'],
                    communication_au_candidat=form.cleaned_data.get('communication_to_the_candidate') or '',
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class CddApprovalFinalDecisionView(
    CddDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'cdd-decision-approval-final'
    urlpatterns = {'cdd-decision-approval-final': 'cdd-decision/cdd-decision-approval-final'}
    template_name = 'admission/doctorate/includes/checklist/cdd_decision_approval_final_form.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/cdd_decision_approval_final_form.html'
    permission_required = 'admission.checklist_change_faculty_decision'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['cdd_decision_approval_final_form'] = self.cdd_decision_approval_final_form
        return context

    def get_form(self, form_class=None):
        return self.cdd_decision_approval_final_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ApprouverPropositionParCddCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    objet_message=form.cleaned_data['subject'],
                    corps_message=form.cleaned_data['body'],
                )
            )
            self.htmx_refresh = True
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class CddDecisionClosedView(
    CddDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'cdd-decision-closed'
    urlpatterns = {'cdd-decision-closed': 'cdd-decision/cdd-decision-closed'}
    template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    permission_required = 'admission.checklist_change_faculty_decision'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                CloturerPropositionParCddCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
            self.htmx_refresh = True
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class CddDecisionToProcessedView(
    CddDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'cdd-decision-to-processed'
    urlpatterns = {'cdd-decision-to-processed': 'cdd-decision/cdd-decision-to-processed'}
    template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    permission_required = 'admission.checklist_change_faculty_decision'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                PasserEtatATraiterDecisionCddCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class CddDecisionTakenInChargeView(
    CddDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'cdd-decision-taken-in-charge'
    urlpatterns = {'cdd-decision-taken-in-charge': 'cdd-decision/cdd-decision-taken-in-charge'}
    template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    permission_required = 'admission.checklist_change_faculty_decision'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                PasserEtatPrisEnChargeDecisionCddCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class CddDecisionToCompleteBySicView(
    CddDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'cdd-decision-to-complete-by-sic'
    urlpatterns = {'cdd-decision-to-complete-by-sic': 'cdd-decision/cdd-decision-to-complete-by-sic'}
    template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/cdd_decision.html'
    permission_required = 'admission.checklist_change_faculty_decision'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                PasserEtatACompleterParSicDecisionCddCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)
