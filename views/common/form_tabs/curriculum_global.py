# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.views.generic import FormView

from admission.ddd.admission.doctorat.preparation.commands import (
    CompleterCurriculumCommand as CompleterCurriculumDoctoratCommand,
)
from admission.ddd.admission.formation_continue.commands import (
    CompleterCurriculumCommand as CompleterCurriculumContinueCommand,
)
from admission.ddd.admission.formation_generale.commands import (
    CompleterCurriculumCommand as CompleterCurriculumGeneraleCommand,
)
from admission.forms.admission.curriculum import GlobalCurriculumForm
from admission.constants import CONTEXT_DOCTORATE, CONTEXT_GENERAL, CONTEXT_CONTINUING
from admission.views.common.detail_tabs.curriculum_global import CurriculumGlobalCommonViewMixin
from admission.views.common.mixins import AdmissionFormMixin
from base.models.enums.education_group_types import TrainingType
from infrastructure.messages_bus import message_bus_instance

__namespace__ = ''

__all__ = [
    'CurriculumGlobalFormView',
]


class CurriculumGlobalFormView(AdmissionFormMixin, CurriculumGlobalCommonViewMixin, FormView):
    urlpatterns = {'curriculum': 'curriculum'}
    template_name = 'admission/forms/curriculum.html'
    permission_required = 'admission.change_admission_curriculum'
    form_class = GlobalCurriculumForm
    extra_context = {
        'force_form': True,
    }

    @cached_property
    def require_equivalence(self):
        return (
            self.proposition.formation.type
            in {
                TrainingType.AGGREGATION.name,
                TrainingType.CAPAES.name,
            }
            and self.curriculum.a_diplome_etranger
            and not self.curriculum.a_diplome_belge
        )

    @cached_property
    def require_curriculum(self):
        return self.proposition.formation.type != TrainingType.BACHELOR.name and (self.is_doctorate or self.is_general)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_item_configurations'] = self.specific_questions
        kwargs['display_equivalence'] = self.display_equivalence
        kwargs['display_curriculum'] = self.display_curriculum
        kwargs['require_equivalence'] = self.require_equivalence
        kwargs['require_curriculum'] = self.require_curriculum
        return kwargs

    def get_initial(self):
        return {
            'reponses_questions_specifiques': self.proposition.reponses_questions_specifiques,
            'curriculum': self.proposition.curriculum,
            'equivalence_diplome': getattr(self.proposition, 'equivalence_diplome', []),
        }

    def form_valid(self, form):
        common_kwargs = dict(
            auteur_modification=self.request.user.person.global_id,
            uuid_proposition=self.admission_uuid,
            reponses_questions_specifiques=form.cleaned_data['reponses_questions_specifiques'],
            curriculum=form.cleaned_data['curriculum'],
        )

        if self.is_continuing:
            message_bus_instance.invoke(
                CompleterCurriculumContinueCommand(
                    equivalence_diplome=form.cleaned_data['equivalence_diplome'],
                    **common_kwargs,
                )
            )
        elif self.is_general:
            message_bus_instance.invoke(
                CompleterCurriculumGeneraleCommand(
                    equivalence_diplome=form.cleaned_data['equivalence_diplome'],
                    **common_kwargs,
                )
            )
        elif self.is_doctorate:
            message_bus_instance.invoke(
                CompleterCurriculumDoctoratCommand(
                    **common_kwargs,
                )
            )

        return super().form_valid(form)

    def get_success_url(self):
        return self.next_url or resolve_url(f'admission:{self.current_context}:curriculum', uuid=self.admission_uuid)
