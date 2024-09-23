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

from django.forms import Form
from django.utils.functional import cached_property
from django.views.generic import FormView, TemplateView
from osis_history.models import HistoryEntry

from admission.ddd.admission.doctorat.preparation.commands import (
    EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand,
    SpecifierInformationsAcceptationPropositionParFaculteCommand,
    ApprouverPropositionParFaculteCommand,
    RefuserPropositionParFaculteCommand,
    EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC_ETENDUS,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC_ETENDUS,
    STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_FAC_POUR_DECISION,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.dtos import PromoteurDTO
from admission.forms.admission.checklist import (
    DoctorateFacDecisionApprovalForm,
    SendEMailForm,
)
from admission.mail_templates import (
    ADMISSION_EMAIL_FAC_REFUSAL_DOCTORATE,
    ADMISSION_EMAIL_FAC_APPROVAL_DOCTORATE_WITH_BELGIAN_DIPLOMA,
    ADMISSION_EMAIL_FAC_APPROVAL_DOCTORATE_WITHOUT_BELGIAN_DIPLOMA,
)
from admission.utils import get_salutation_prefix
from admission.views.common.detail_tabs.checklist import change_admission_status
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from admission.views.doctorate.details.checklist.mixins import CheckListDefaultContextMixin, get_email
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'FacultyDecisionView',
    'FacultyDecisionSendToFacultyView',
    'FacultyRefusalDecisionView',
    'FacultyApprovalDecisionView',
    'FacultyDecisionSendToSicView',
    'FacultyApprovalFinalDecisionView',
]


__namespace__ = False


# Fac decision
class FacultyDecisionMixin(CheckListDefaultContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['in_sic_statuses'] = self.admission.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC_ETENDUS
        context['in_fac_statuses'] = self.admission.status in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC_ETENDUS
        context['sic_statuses_for_transfer'] = ChoixStatutPropositionDoctorale.get_specific_values(
            STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_FAC_POUR_DECISION
        )
        context['fac_statuses_for_transfer'] = ChoixStatutPropositionDoctorale.get_specific_values(
            STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC
        )
        context['is_fac'] = self.is_fac
        context['is_sic'] = self.is_sic

        context.setdefault('history_entries', {})

        faculty_decision_history = (
            HistoryEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__contains=['proposition', 'fac-decision', 'message'],
            )
            .order_by('-created')
            .first()
        )

        context['history_entries']['fac_decision'] = faculty_decision_history

        context['fac_decision_refusal_form'] = self.fac_decision_refusal_form
        context['fac_decision_approval_form'] = self.fac_decision_approval_form
        context['fac_decision_approval_final_form'] = self.fac_decision_approval_final_form

        return context

    @cached_property
    def fac_decision_refusal_form(self):
        form_kwargs = {
            'prefix': 'fac-decision-refusal',
        }

        if self.request.method == 'GET':
            # Load the email template
            subject, body = get_email(
                template_identifier=ADMISSION_EMAIL_FAC_REFUSAL_DOCTORATE,
                language=self.proposition.langue_contact_candidat,
                proposition_dto=self.proposition,
                extra_tokens={
                    'greetings': get_salutation_prefix(self.admission.candidate),
                    'doctoral_commission': self.management_entity_title,
                    'sender_name': f'{self.request.user.person.first_name} {self.request.user.person.last_name}',
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
    def fac_decision_approval_final_form(self):
        form_kwargs = {
            'prefix': 'fac-decision-approval-final',
        }

        if self.request.method == 'GET':
            # Load the email template
            subject, body = get_email(
                template_identifier=ADMISSION_EMAIL_FAC_APPROVAL_DOCTORATE_WITH_BELGIAN_DIPLOMA
                if self.proposition_resume.resume.curriculum.a_diplome_belge
                else ADMISSION_EMAIL_FAC_APPROVAL_DOCTORATE_WITHOUT_BELGIAN_DIPLOMA,
                language=self.proposition.langue_contact_candidat,
                proposition_dto=self.proposition,
                extra_tokens={
                    'greetings': get_salutation_prefix(self.admission.candidate),
                    'doctoral_commission': self.management_entity_title,
                    'sender_name': f'{self.request.user.person.first_name} {self.request.user.person.last_name}',
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
    def fac_decision_approval_form(self):
        initial = {}

        if (
            self.request.method == 'GET'
            and self.proposition_resume.resume.groupe_supervision
            and self.proposition_resume.resume.groupe_supervision.promoteur_reference_dto
        ):
            reference_promoter: PromoteurDTO = self.proposition_resume.resume.groupe_supervision.promoteur_reference_dto

            initial['annual_program_contact_person_name'] = f'{reference_promoter.prenom} {reference_promoter.nom}'
            initial['annual_program_contact_person_email'] = reference_promoter.email

        return DoctorateFacDecisionApprovalForm(
            academic_year=self.admission.determined_academic_year.year,
            instance=self.admission if self.request.method != 'POST' else None,
            initial=initial,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='fac-decision-approval',
        )


class FacultyDecisionView(
    AdmissionFormMixin,
    FacultyDecisionMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'fac-decision-status'
    urlpatterns = {'fac-decision-change-status': 'fac-decision/status-change/<str:status>'}
    permission_required = 'admission.checklist_change_faculty_decision'
    template_name = 'admission/doctorate/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/fac_decision.html'
    form_class = Form

    def form_valid(self, form):
        admission = self.get_permission_object()

        extra = {}
        if 'decision' in self.request.GET:
            extra['decision'] = self.request.GET['decision']

        change_admission_status(
            tab='decision_facultaire',
            admission_status=self.kwargs['status'],
            extra=extra,
            admission=admission,
            replace_extra=True,
            author=self.request.user.person,
        )

        return super().form_valid(form)


class FacultyDecisionSendToFacultyView(
    AdmissionFormMixin,
    FacultyDecisionMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'faculty-decision-send-to-faculty'
    urlpatterns = {'fac-decision-send-to-faculty': 'fac-decision/send-to-faculty'}
    permission_required = 'admission.checklist_faculty_decision_transfer_to_fac'
    template_name = 'admission/doctorate/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/fac_decision.html'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)
        self.htmx_refresh = True
        return super().form_valid(form)


class FacultyDecisionSendToSicView(
    AdmissionFormMixin,
    FacultyDecisionMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'faculty-decision-send-to-sic'
    urlpatterns = {'fac-decision-send-to-sic': 'fac-decision/send-to-sic'}
    template_name = 'admission/doctorate/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/fac_decision.html'
    form_class = Form
    permission_required = 'admission.checklist_faculty_decision_transfer_to_sic_without_decision'

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    envoi_par_fac=self.is_fac,
                )
            )

        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        self.htmx_refresh = True

        return super().form_valid(form)


class FacultyRefusalDecisionView(
    FacultyDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'fac-decision-refusal'
    urlpatterns = {'fac-decision-refusal': 'fac-decision/fac-decision-refusal'}
    template_name = 'admission/doctorate/includes/checklist/fac_decision_refusal_form.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/fac_decision_refusal_form.html'
    permission_required = 'admission.checklist_change_faculty_decision'

    def get_form(self, form_class=None):
        return self.fac_decision_refusal_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                RefuserPropositionParFaculteCommand(
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


class FacultyApprovalDecisionView(
    FacultyDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'fac-decision-approval'
    urlpatterns = {'fac-decision-approval': 'fac-decision/fac-decision-approval'}
    template_name = 'admission/doctorate/includes/checklist/fac_decision_approval_form.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/fac_decision_approval_form.html'
    permission_required = 'admission.checklist_change_faculty_decision'

    def get_form(self, form_class=None):
        return self.fac_decision_approval_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierInformationsAcceptationPropositionParFaculteCommand(
                    uuid_proposition=self.admission_uuid,
                    avec_complements_formation=form.cleaned_data['with_prerequisite_courses'],
                    uuids_complements_formation=form.cleaned_data['prerequisite_courses'],
                    commentaire_complements_formation=form.cleaned_data['prerequisite_courses_fac_comment'],
                    nombre_annees_prevoir_programme=form.cleaned_data['program_planned_years_number'],
                    nom_personne_contact_programme_annuel=form.cleaned_data['annual_program_contact_person_name'],
                    email_personne_contact_programme_annuel=form.cleaned_data['annual_program_contact_person_email'],
                    commentaire_programme_conjoint=form.cleaned_data['join_program_fac_comment'],
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class FacultyApprovalFinalDecisionView(
    FacultyDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'fac-decision-approval-final'
    urlpatterns = {'fac-decision-approval-final': 'fac-decision/fac-decision-approval-final'}
    template_name = 'admission/doctorate/includes/checklist/fac_decision_approval_final_form.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/fac_decision_approval_final_form.html'
    permission_required = 'admission.checklist_change_faculty_decision'

    def get_form(self, form_class=None):
        return self.fac_decision_approval_final_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ApprouverPropositionParFaculteCommand(
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
