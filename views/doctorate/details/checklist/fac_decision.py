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

from django.db.models import QuerySet
from django.forms import Form
from django.forms.formsets import formset_factory
from django.utils.functional import cached_property
from django.views.generic import FormView
from osis_history.models import HistoryEntry

from admission.ddd.admission.doctorat.preparation.commands import (
    EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand,
    SpecifierMotifsRefusPropositionParFaculteCommand,
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
from admission.ddd.admission.shared_kernel.email_destinataire.domain.validator.exceptions import (
    InformationsDestinatairePasTrouvee,
)
from admission.ddd.admission.shared_kernel.email_destinataire.queries import RecupererInformationsDestinataireQuery
from admission.forms.admission.checklist import (
    FacDecisionRefusalForm,
    FacDecisionApprovalForm,
    DoctorateFacDecisionApprovalForm,
)
from admission.forms.admission.checklist import (
    FreeAdditionalApprovalConditionForm,
)
from admission.views.common.detail_tabs.checklist import change_admission_status
from admission.views.common.mixins import AdmissionFormMixin
from admission.views.doctorate.details.checklist.mixins import CheckListDefaultContextMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_profile.models import EducationalExperience

__all__ = [
    'FacultyDecisionView',
    'FacultyDecisionSendToFacultyView',
    'FacultyRefusalDecisionView',
    'FacultyApprovalDecisionView',
    'FacultyDecisionSendToSicView',
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
        context['fac_decision_send_to_fac_history_entry'] = (
            HistoryEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__contains=['proposition', 'fac-decision', 'send-to-fac'],
            )
            .order_by('-created')
            .first()
        )
        context['fac_decision_refusal_form'] = self.fac_decision_refusal_form
        context['fac_decision_approval_form'] = self.fac_decision_approval_form
        context['fac_decision_free_approval_condition_formset'] = self.fac_decision_free_approval_condition_formset
        context['program_faculty_email'] = self.program_faculty_email.email if self.program_faculty_email else None

        return context

    @cached_property
    def program_faculty_email(self):
        try:
            return message_bus_instance.invoke(
                RecupererInformationsDestinataireQuery(
                    sigle_formation=self.admission.training.acronym,
                    est_premiere_annee=False,
                    annee=self.admission.determined_academic_year.year,
                )
            )
        except InformationsDestinatairePasTrouvee:
            return None

    @cached_property
    def fac_decision_refusal_form(self):
        form_kwargs = {
            'prefix': 'fac-decision-refusal',
        }
        if self.request.method == 'POST':
            form_kwargs['data'] = self.request.POST
        else:
            form_kwargs['initial'] = {
                'reasons': [reason.uuid for reason in self.admission.refusal_reasons.all()]
                + self.admission.other_refusal_reasons,
            }

        return FacDecisionRefusalForm(**form_kwargs)

    @property
    def candidate_cv_program_names_by_experience_uuid(self):
        experiences: QuerySet[EducationalExperience] = EducationalExperience.objects.select_related('program').filter(
            person=self.admission.candidate
        )
        return {
            str(experience.uuid): experience.program.title if experience.program else experience.education_name
            for experience in experiences
        }

    @cached_property
    def fac_decision_approval_form(self):
        return DoctorateFacDecisionApprovalForm(
            academic_year=self.admission.determined_academic_year.year,
            instance=self.admission if self.request.method != 'POST' else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='fac-decision-approval',
            educational_experience_program_name_by_uuid=self.candidate_cv_program_names_by_experience_uuid,
            current_training_uuid=str(self.admission.training.uuid),
        )

    @cached_property
    def fac_decision_free_approval_condition_formset(self):
        FreeApprovalConditionFormSet = formset_factory(
            form=FreeAdditionalApprovalConditionForm,
            extra=0,
        )

        formset = FreeApprovalConditionFormSet(
            prefix='fac-decision',
            initial=self.admission.freeadditionalapprovalcondition_set.filter(
                related_experience__isnull=True,
            ).values('name_fr', 'name_en')
            if self.request.method != 'POST'
            else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            form_kwargs={
                'candidate_language': self.admission.candidate.language,
            },
        )

        return formset


class FacultyDecisionView(
    AdmissionFormMixin,
    FacultyDecisionMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'fac-decision-status'
    urlpatterns = {'fac-decision-change-status': 'fac-decision/status-change/<str:status>'}
    permission_required = 'admission.checklist_change_faculty_decision'
    template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision.html'
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
    template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision.html'
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
    template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    form_class = Form

    def get_permission_required(self):
        return (
            ('admission.checklist_faculty_decision_transfer_to_sic_with_decision',)
            if (self.request.GET.get('approval') or self.request.GET.get('refusal')) and self.is_fac
            else ('admission.checklist_faculty_decision_transfer_to_sic_without_decision',)
        )

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ApprouverPropositionParFaculteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
                if self.request.GET.get('approval') and self.is_fac
                else RefuserPropositionParFaculteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
                if self.request.GET.get('refusal') and self.is_fac
                else EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand(
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
    template_name = 'admission/general_education/includes/checklist/fac_decision_refusal_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision_refusal_form.html'

    def get_permission_required(self):
        return (
            (
                'admission.checklist_faculty_decision_transfer_to_sic_with_decision'
                if 'save_transfer' in self.request.POST
                else 'admission.checklist_change_faculty_decision'
            ),
        )

    def get_form(self, form_class=None):
        return self.fac_decision_refusal_form

    def form_valid(self, form):
        base_params = {
            'uuid_proposition': self.admission_uuid,
            'uuids_motifs': form.cleaned_data['reasons'],
            'autres_motifs': form.cleaned_data['other_reasons'],
            'gestionnaire': self.request.user.person.global_id,
        }

        try:
            message_bus_instance.invoke(SpecifierMotifsRefusPropositionParFaculteCommand(**base_params))
            if 'save-transfer' in self.request.POST:
                message_bus_instance.invoke(
                    RefuserPropositionParFaculteCommand(
                        uuid_proposition=self.admission_uuid,
                        gestionnaire=self.request.user.person.global_id,
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
    template_name = 'admission/general_education/includes/checklist/fac_decision_approval_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision_approval_form.html'

    def get_permission_required(self):
        return (
            (
                'admission.checklist_faculty_decision_transfer_to_sic_with_decision'
                if 'save_transfer' in self.request.POST
                else 'admission.checklist_change_faculty_decision'
            ),
        )

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = self.fac_decision_free_approval_condition_formset

        # Cross validation
        if form.is_valid() and formset.is_valid():
            with_additional_conditions = form.cleaned_data['with_additional_approval_conditions']

            if with_additional_conditions and (
                not form.cleaned_data['additional_approval_conditions']
                and not form.cleaned_data['cv_experiences_additional_approval_conditions']
                and not any(subform.is_valid() for subform in formset)
            ):
                form.add_error('all_additional_approval_conditions', FIELD_REQUIRED_MESSAGE)

        form.all_required_forms_are_valid = form.is_valid() and (
            not form.cleaned_data['with_additional_approval_conditions'] or formset.is_valid()
        )

        if form.all_required_forms_are_valid:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form(self, form_class=None):
        return self.fac_decision_approval_form

    def form_valid(self, form):
        base_params = {
            'uuid_proposition': self.admission_uuid,
            'sigle_autre_formation': form.cleaned_data['other_training_accepted_by_fac'].acronym
            if form.cleaned_data['other_training_accepted_by_fac']
            else '',
            'avec_conditions_complementaires': form.cleaned_data['with_additional_approval_conditions'],
            'uuids_conditions_complementaires_existantes': [
                condition for condition in form.cleaned_data['additional_approval_conditions']
            ],
            'conditions_complementaires_libres': (
                [
                    sub_form.cleaned_data
                    for sub_form in self.fac_decision_free_approval_condition_formset.forms
                    if sub_form.is_valid()
                ]
                if form.cleaned_data['with_additional_approval_conditions']
                else []
            )
            + form.cleaned_data['cv_experiences_additional_approval_conditions'],
            'avec_complements_formation': form.cleaned_data['with_prerequisite_courses'],
            'uuids_complements_formation': form.cleaned_data['prerequisite_courses'],
            'commentaire_complements_formation': form.cleaned_data['prerequisite_courses_fac_comment'],
            'nombre_annees_prevoir_programme': form.cleaned_data['program_planned_years_number'],
            'nom_personne_contact_programme_annuel': form.cleaned_data['annual_program_contact_person_name'],
            'email_personne_contact_programme_annuel': form.cleaned_data['annual_program_contact_person_email'],
            'commentaire_programme_conjoint': form.cleaned_data['join_program_fac_comment'],
            'gestionnaire': self.request.user.person.global_id,
        }
        try:
            message_bus_instance.invoke(SpecifierInformationsAcceptationPropositionParFaculteCommand(**base_params))
            if 'save-transfer' in self.request.POST:
                message_bus_instance.invoke(
                    ApprouverPropositionParFaculteCommand(
                        uuid_proposition=self.admission_uuid,
                        gestionnaire=self.request.user.person.global_id,
                    )
                )
                self.htmx_refresh = True
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)
