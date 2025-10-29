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
from typing import Optional

from django.forms import Form
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from osis_comment.models import CommentEntry
from osis_history.models import HistoryEntry

from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierAuthentificationExperienceParcoursAnterieurCommand,
    ModifierStatutChecklistExperienceParcoursAnterieurCommand,
    ModifierStatutChecklistParcoursAnterieurCommand,
    SpecifierConditionAccesPropositionCommand,
    VerifierExperienceCurriculumApresSoumissionQuery,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    OngletsChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    ConditionAccesEtreSelectionneException,
    ExperiencesAcademiquesNonCompleteesException,
    TitreAccesEtreSelectionneException,
)
from admission.ddd.admission.shared_kernel.commands import (
    SpecifierExperienceEnTantQueTitreAccesCommand,
)
from admission.ddd.admission.shared_kernel.domain.model.enums.authentification import (
    EtatAuthentificationParcours,
)
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import (
    ExperienceNonTrouveeException,
)
from admission.forms.admission.checklist import (
    CommentForm,
    DoctoratePastExperiencesAdmissionRequirementForm,
    ExperienceStatusForm,
    SinglePastExperienceAuthenticationForm,
    StatusForm,
    can_edit_experience_authentication,
)
from admission.templatetags.admission import authentication_css_class
from admission.utils import get_missing_curriculum_periods_for_doctorate
from admission.views.common.detail_tabs.checklist import ChecklistTabIcon
from admission.views.common.mixins import AdmissionFormMixin, AdmissionViewMixin
from admission.views.doctorate.details.checklist.mixins import (
    CheckListDefaultContextMixin,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException

__all__ = [
    'MissingCurriculumPeriodsView',
    'PastExperiencesStatusView',
    'PastExperiencesAdmissionRequirementView',
    'PastExperiencesAccessTitleView',
    'SinglePastExperienceChangeStatusView',
    'SinglePastExperienceChangeAuthenticationView',
]


__namespace__ = False


class PastExperiencesMixin:
    @cached_property
    def past_experiences_admission_requirement_form(self):
        return DoctoratePastExperiencesAdmissionRequirementForm(instance=self.admission, data=self.request.POST or None)

    @property
    def access_title_url(self):
        return resolve_url(
            f'{self.base_namespace}:past-experiences-access-title',
            uuid=self.kwargs['uuid'],
        )


class PastExperiencesStatusView(
    AdmissionFormMixin,
    CheckListDefaultContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'past-experiences-status'
    urlpatterns = {'past-experiences-change-status': 'past-experiences-change-status/<str:status>'}
    permission_required = 'admission.change_checklist'
    template_name = 'admission/general_education/includes/checklist/previous_experiences.html'
    htmx_template_name = 'admission/general_education/includes/checklist/previous_experiences.html'
    form_class = StatusForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['past_experiences_admission_requirement_form'] = DoctoratePastExperiencesAdmissionRequirementForm(
            instance=self.admission,
        )
        return context

    def get_initial(self):
        return self.admission.checklist['current']['parcours_anterieur']['statut']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['data'] = self.kwargs
        return kwargs

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ModifierStatutChecklistParcoursAnterieurCommand(
                    uuid_proposition=self.admission_uuid,
                    statut=form.cleaned_data['status'],
                    gestionnaire=self.request.user.person.global_id,
                )
            )
            self.htmx_trigger_form_extra = {
                'select_access_title_perm': self.request.user.has_perm(
                    'admission.checklist_select_access_title',
                    self.admission,
                ),
            }
            if (
                self.admission.checklist['current']['parcours_anterieur']['statut']
                == ChoixStatutChecklist.GEST_REUSSITE.name
            ):
                self.htmx_trigger_form_extra['select_access_title_tooltip'] = gettext(
                    'Changes for the access title are not available when the state of the Previous experience '
                    'is "Sufficient".'
                )
        except MultipleBusinessExceptions as exceptions:
            error_messages = set()

            for exception in exceptions.exceptions:
                if isinstance(exception, (TitreAccesEtreSelectionneException, ConditionAccesEtreSelectionneException)):
                    error_messages.add(
                        gettext(
                            'To move to this state, an admission requirement must have been selected and at least'
                            ' one access title line must be selected in the past experience views.'
                        )
                    )
                else:
                    error_messages.add(str(exception.message))

                self.htmx_trigger_form_extra = {'error_messages': list(error_messages)}

            return super().form_invalid(form)

        return super().form_valid(form)


class PastExperiencesAdmissionRequirementView(
    PastExperiencesMixin,
    AdmissionFormMixin,
    CheckListDefaultContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'past-experiences-admission-requirement'
    urlpatterns = 'past-experiences-admission-requirement'
    permission_required = 'admission.change_checklist'
    template_name = (
        'admission/general_education/includes/checklist/previous_experiences_admission_requirement_form.html'
    )
    htmx_template_name = (
        'admission/general_education/includes/checklist/previous_experiences_admission_requirement_form.html'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['past_experiences_admission_requirement_form'] = context['form']
        return context

    def get_form(self, form_class=None):
        return self.past_experiences_admission_requirement_form

    def reset_form_data(self, form):
        form.data = {
            'admission_requirement': self.admission.admission_requirement,
            'admission_requirement_year': self.admission.admission_requirement_year_id,
            'with_prerequisite_courses': self.admission.with_prerequisite_courses,
        }

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierConditionAccesPropositionCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    condition_acces=form.cleaned_data['admission_requirement'],
                    millesime_condition_acces=form.cleaned_data['admission_requirement_year']
                    and form.cleaned_data['admission_requirement_year'].year,
                )
            )

            # The admission requirement year can be updated via the command
            self.reset_form_data(form)

        except (BusinessException, MultipleBusinessExceptions) as exception:
            self.message_on_failure = (
                exception.exceptions.pop().message
                if isinstance(exception, MultipleBusinessExceptions)
                else exception.message
            )

            self.reset_form_data(form)

            return super().form_invalid(form)

        return super().form_valid(form)


class PastExperiencesAccessTitleView(
    PastExperiencesMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'past-experiences-access-title'
    urlpatterns = 'past-experiences-access-title'
    permission_required = 'admission.checklist_select_access_title'
    template_name = 'admission/general_education/includes/checklist/parcours_row_access_title.html'
    htmx_template_name = 'admission/general_education/includes/checklist/parcours_row_access_title.html'
    form_class = Form

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checked: Optional[bool] = None
        self.experience_uuid: str = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['checked'] = self.checked
        context['url'] = self.request.get_full_path()
        context['experience_uuid'] = self.request.GET.get('experience_uuid')
        context['can_choose_access_title'] = True  # True as the user can access to the current view

        return context

    def form_valid(self, form):
        experience_type = self.request.GET.get('experience_type')
        self.experience_uuid = self.request.GET.get('experience_uuid')
        self.checked = 'access-title' in self.request.POST
        try:
            message_bus_instance.invoke(
                SpecifierExperienceEnTantQueTitreAccesCommand(
                    uuid_proposition=self.admission_uuid,
                    uuid_experience=self.experience_uuid,
                    selectionne=self.checked,
                    type_experience=experience_type,
                )
            )

        except BusinessException as exception:
            self.message_on_failure = exception.message
            self.checked = not self.checked
            return super().form_invalid(form)

        return super().form_valid(form)


class SinglePastExperienceMixin(
    PastExperiencesMixin,
    AdmissionFormMixin,
    CheckListDefaultContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    @cached_property
    def experience_uuid(self):
        return self.request.GET.get('identifier')

    @cached_property
    def experience_type(self):
        return self.request.GET.get('type', '')

    @property
    def experience(self):
        return next(
            (
                experience
                for experience in self.admission.checklist['current']['parcours_anterieur']['enfants']
                if experience['extra']['identifiant'] == self.experience_uuid
            ),
            None,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experience = self.experience
        context['current'] = experience
        context['initial'] = self.experience or {}
        context['experience_type'] = self.experience_type
        authentication_comment_identifier = f'parcours_anterieur__{self.experience_uuid}__authentication'
        context.setdefault('comment_forms', {})
        context['comment_forms'][authentication_comment_identifier] = CommentForm(
            comment=CommentEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags=['parcours_anterieur', self.experience_uuid, 'authentication'],
            )
            .select_related('author')
            .first(),
            form_url=resolve_url(
                f'{self.base_namespace}:save-comment',
                uuid=self.admission_uuid,
                tab=authentication_comment_identifier,
            ),
            prefix=authentication_comment_identifier,
            disabled=not can_edit_experience_authentication(self.experience),
            label=_('Comment about the authentication'),
        )
        context['experience_authentication_history_entry'] = (
            HistoryEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__contains=['proposition', 'experience-authentication', 'message'],
                extra_data__experience_id=self.experience_uuid,
            )
            .order_by('-created')
            .first()
        )

        if experience:
            tab_identifier = f'parcours_anterieur__{self.experience_uuid}'
            experience_authentication_state = experience['extra'].get('etat_authentification') or ''
            context['checklist_additional_icons'][tab_identifier].append(
                ChecklistTabIcon(
                    identifier='authentication_state',
                    icon=authentication_css_class(authentication_status=experience_authentication_state),
                    title=EtatAuthentificationParcours.get_value(experience_authentication_state),
                    displayed=bool(experience_authentication_state),
                )
            )
        return context

    def get_success_url(self):
        return self.request.get_full_path()

    def command(self, form):
        raise NotImplementedError

    def form_valid(self, form):
        try:
            self.command(form)
        except ExperienceNonTrouveeException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)
        except MultipleBusinessExceptions as exception:
            self.message_on_failure = exception.exceptions.pop().message
            return super().form_invalid(form)
        return super().form_valid(form)

    @cached_property
    def incomplete_curriculum_experiences(self):
        # Override it to only check a single experience
        try:
            message_bus_instance.invoke(
                VerifierExperienceCurriculumApresSoumissionQuery(
                    uuid_proposition=self.admission_uuid,
                    uuid_experience=self.experience_uuid,
                    type_experience=self.experience_type,
                )
            )
            return set()
        except MultipleBusinessExceptions as multiple_exceptions:
            return {
                str(e.reference)
                for e in multiple_exceptions.exceptions
                if isinstance(e, ExperiencesAcademiquesNonCompleteesException)
            }


class SinglePastExperienceChangeStatusView(SinglePastExperienceMixin):
    name = 'single-past-experience-change-status'
    urlpatterns = 'single-past-experience-change-status'
    permission_required = 'admission.checklist_change_past_experiences'
    template_name = 'admission/general_education/includes/checklist/previous_experience_single.html'
    htmx_template_name = 'admission/general_education/includes/checklist/previous_experience_single.html'
    form_class = ExperienceStatusForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['authentication_form'] = SinglePastExperienceAuthenticationForm(self.experience)
        return context

    def command(self, form):
        message_bus_instance.invoke(
            ModifierStatutChecklistExperienceParcoursAnterieurCommand(
                uuid_proposition=self.admission_uuid,
                uuid_experience=self.experience_uuid,
                type_experience=self.experience_type,
                gestionnaire=self.request.user.person.global_id,
                statut=form.cleaned_data['status'],
                statut_authentification=form.cleaned_data['authentification'],
            )
        )


class SinglePastExperienceChangeAuthenticationView(SinglePastExperienceMixin):
    name = 'single-past-experience-change-authentication'
    urlpatterns = 'single-past-experience-change-authentication'
    permission_required = 'admission.checklist_change_past_experiences'
    template_name = 'admission/general_education/includes/checklist/previous_experience_single_authentication_form.html'
    htmx_template_name = (
        'admission/general_education/includes/checklist/previous_experience_single_authentication_form.html'
    )
    form_class = SinglePastExperienceAuthenticationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['checklist_experience_data'] = self.experience
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['authentication_form'] = context['form']
        return context

    def command(self, form):
        message_bus_instance.invoke(
            ModifierAuthentificationExperienceParcoursAnterieurCommand(
                uuid_proposition=self.admission_uuid,
                uuid_experience=self.experience_uuid,
                gestionnaire=self.request.user.person.global_id,
                etat_authentification=form.cleaned_data['state'],
            )
        )


class MissingCurriculumPeriodsView(AdmissionViewMixin, TemplateView):
    urlpatterns = 'missing-curriculum-periods'
    template_name = 'admission/general_education/includes/checklist/missing_curriculum_periods_message_htmx.html'
    permission_required = 'admission.view_checklist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['missing_curriculum_periods'] = get_missing_curriculum_periods_for_doctorate(
            proposition_uuid=self.admission_uuid,
        )

        context['tabs'] = [
            OngletsChecklist.parcours_anterieur.name,
            OngletsChecklist.financabilite.name,
        ]

        return context
