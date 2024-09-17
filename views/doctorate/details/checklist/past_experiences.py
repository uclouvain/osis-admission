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
from typing import Dict, Optional

from django.forms import Form
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from osis_comment.models import CommentEntry
from osis_history.models import HistoryEntry

from admission.ddd.admission.commands import (
    RecupererTitresAccesSelectionnablesPropositionQuery,
    SpecifierExperienceEnTantQueTitreAccesCommand,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererResumePropositionQuery,
    ModifierStatutChecklistParcoursAnterieurCommand,
    SpecifierConditionAccesPropositionCommand,
    SpecifierEquivalenceTitreAccesEtrangerPropositionCommand,
    ModifierStatutChecklistExperienceParcoursAnterieurCommand,
    ModifierAuthentificationExperienceParcoursAnterieurCommand,
)
from admission.ddd.admission.domain.model.enums.condition_acces import TypeTitreAccesSelectionnable
from admission.ddd.admission.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.ddd.admission.dtos.resume import (
    ResumePropositionDTO,
)
from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from admission.forms.admission.checklist import (
    StatusForm,
    CommentForm,
    can_edit_experience_authentication,
    ExperienceStatusForm,
    SinglePastExperienceAuthenticationForm,
    DoctoratePastExperiencesAdmissionRequirementForm,
    DoctoratePastExperiencesAdmissionAccessTitleForm,
)
from admission.utils import (
    get_access_titles_names,
)
from admission.views.common.mixins import AdmissionFormMixin
from admission.views.doctorate.details.checklist.mixins import CheckListDefaultContextMixin, get_internal_experiences
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException

__all__ = [
    'PastExperiencesStatusView',
    'PastExperiencesAdmissionRequirementView',
    'PastExperiencesAccessTitleEquivalencyView',
    'PastExperiencesAccessTitleView',
    'SinglePastExperienceChangeStatusView',
    'SinglePastExperienceChangeAuthenticationView',
]


__namespace__ = False


class PastExperiencesMixin:
    @cached_property
    def past_experiences_admission_requirement_form(self):
        return DoctoratePastExperiencesAdmissionRequirementForm(instance=self.admission, data=self.request.POST or None)

    @cached_property
    def past_experiences_admission_access_title_equivalency_form(self):
        return DoctoratePastExperiencesAdmissionAccessTitleForm(instance=self.admission, data=self.request.POST or None)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.valid_operation = False

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
            self.valid_operation = True
        except MultipleBusinessExceptions:
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
                    avec_complements_formation=form.cleaned_data['with_prerequisite_courses'],
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

        # Get the list of the selected access titles
        access_titles: Dict[str, TitreAccesSelectionnableDTO] = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=self.admission_uuid,
                seulement_selectionnes=True,
            )
        )

        if access_titles:
            command_result: ResumePropositionDTO = message_bus_instance.invoke(
                RecupererResumePropositionQuery(uuid_proposition=self.admission_uuid),
            )

            internal_experiences = []

            if any(
                title.type_titre == TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE.name
                for title in access_titles.values()
            ):
                internal_experiences = get_internal_experiences(
                    matricule_candidat=command_result.proposition.matricule_candidat,
                )

            context['selected_access_titles_names'] = get_access_titles_names(
                access_titles=access_titles,
                curriculum_dto=command_result.curriculum,
                etudes_secondaires_dto=command_result.etudes_secondaires,
                internal_experiences=internal_experiences,
            )

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


class PastExperiencesAccessTitleEquivalencyView(
    PastExperiencesMixin,
    AdmissionFormMixin,
    CheckListDefaultContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'past-experiences-access-title-equivalency'
    urlpatterns = 'past-experiences-access-title-equivalency'
    permission_required = 'admission.change_checklist'
    template_name = (
        'admission/general_education/includes/checklist/previous_experiences_access_title_equivalency_form.html'
    )
    htmx_template_name = (
        'admission/general_education/includes/checklist/previous_experiences_access_title_equivalency_form.html'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['past_experiences_admission_access_title_equivalency_form'] = context['form']
        return context

    def get_form(self, form_class=None):
        return self.past_experiences_admission_access_title_equivalency_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierEquivalenceTitreAccesEtrangerPropositionCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    type_equivalence_titre_acces=form.cleaned_data['foreign_access_title_equivalency_type'],
                    information_a_propos_de_la_restriction=form.cleaned_data[
                        'foreign_access_title_equivalency_restriction_about'
                    ],
                    statut_equivalence_titre_acces=form.cleaned_data['foreign_access_title_equivalency_status'],
                    etat_equivalence_titre_acces=form.cleaned_data['foreign_access_title_equivalency_state'],
                    date_prise_effet_equivalence_titre_acces=form.cleaned_data[
                        'foreign_access_title_equivalency_effective_date'
                    ],
                )
            )

        except MultipleBusinessExceptions as exception:
            self.message_on_failure = exception.exceptions.pop().message
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
        context['current'] = self.experience
        context['initial'] = self.experience or {}
        authentication_comment_identifier = f'parcours_anterieur__{self.experience_uuid}__authentication'
        context.setdefault('comment_forms', {})
        context['comment_forms'][authentication_comment_identifier] = CommentForm(
            comment=CommentEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags=['parcours_anterieur', self.experience_uuid, 'authentication'],
            ).first(),
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
        return super().form_valid(form)


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
