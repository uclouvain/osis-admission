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
from attr import asdict
from django.urls import reverse
from django.views.generic import FormView

from admission.ddd.admission.formation_generale.commands import CompleterQuestionsSpecifiquesParGestionnaireCommand
from admission.forms.admission.specific_questions import GeneralSpecificQuestionsForm
from admission.views.common.detail_tabs.specific_questions import SpecificQuestionsMixinView
from infrastructure.messages_bus import message_bus_instance


__all__ = [
    'SpecificQuestionsFormView',
]


class SpecificQuestionsFormView(SpecificQuestionsMixinView, FormView):
    template_name = 'admission/forms/specific_questions.html'
    permission_required = 'admission.change_admission_specific_questions'
    urlpatterns = 'specific-questions'

    def get_form_class(self):
        if self.is_general:
            return GeneralSpecificQuestionsForm

    def get_initial(self):
        initial_data = asdict(self.proposition)
        initial_data['poste_diplomatique'] = (
            self.proposition.poste_diplomatique.code if self.proposition.poste_diplomatique else None
        )
        return initial_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs['form_item_configurations'] = self.specific_questions

        if self.is_general:
            kwargs['display_visa'] = self.display_visa_question
            kwargs['residential_country'] = self.identification_dto.pays_residence
            kwargs['display_pool_questions'] = self.display_pool_questions
            kwargs['enrolled_for_contingent_training'] = self.enrolled_for_contingent_training

        return kwargs

    def form_valid(self, form):
        if self.is_general:
            message_bus_instance.invoke(
                CompleterQuestionsSpecifiquesParGestionnaireCommand(
                    uuid_proposition=self.proposition.uuid,
                    **form.cleaned_data,
                )
            )
        return super().form_valid(form)

    def get_success_url(self):
        return self.next_url or reverse(f'admission:{self.current_context}:specific-questions', kwargs=self.kwargs)
