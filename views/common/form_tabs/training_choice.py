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
from django.urls import reverse
from django.views.generic import FormView

from admission.constants import CONTEXT_GENERAL, CONTEXT_CONTINUING, CONTEXT_DOCTORATE
from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierChoixFormationParGestionnaireCommand as ModifierChoixFormationDoctoraleParGestionnaireCommand,
)
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_continue.commands import (
    ModifierChoixFormationParGestionnaireCommand as ModifierChoixFormationContinueParGestionnaireCommand,
)
from admission.ddd.admission.formation_generale.commands import (
    ModifierChoixFormationParGestionnaireCommand as ModifierChoixFormationGeneraleParGestionnaireCommand,
)
from admission.forms.admission.training_choice import (
    GeneralTrainingChoiceForm,
    ContinuingTrainingChoiceForm,
    DoctorateTrainingChoiceForm,
)
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = ['AdmissionTrainingChoiceFormView']


class AdmissionTrainingChoiceFormView(AdmissionFormMixin, LoadDossierViewMixin, FormView):
    template_name = 'admission/forms/training_choice.html'
    permission_required = 'admission.change_admission_training_choice'
    update_requested_documents = True
    urlpatterns = 'training-choice'
    specific_questions_tab = Onglets.CHOIX_FORMATION

    def get_form_class(self):
        return {
            CONTEXT_GENERAL: GeneralTrainingChoiceForm,
            CONTEXT_CONTINUING: ContinuingTrainingChoiceForm,
            CONTEXT_DOCTORATE: DoctorateTrainingChoiceForm,
        }[self.current_context]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proposition'] = self.proposition
        kwargs['user'] = self.request.user
        kwargs['form_item_configurations'] = self.specific_questions
        return kwargs

    def form_valid(self, form):
        if self.is_general:
            message_bus_instance.invoke(
                ModifierChoixFormationGeneraleParGestionnaireCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    bourse_double_diplome=form.cleaned_data['double_degree_scholarship'],
                    bourse_internationale=form.cleaned_data['international_scholarship'],
                    bourse_erasmus_mundus=form.cleaned_data['erasmus_mundus_scholarship'],
                    reponses_questions_specifiques=form.cleaned_data['specific_question_answers'],
                )
            )

        elif self.is_continuing:
            message_bus_instance.invoke(
                ModifierChoixFormationContinueParGestionnaireCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    sigle_formation=form.cleaned_data['continuing_education_training'],
                    annee_formation=form.cleaned_data['academic_year'].year,
                    reponses_questions_specifiques=form.cleaned_data['specific_question_answers'],
                    motivations=form.cleaned_data['motivations'],
                    moyens_decouverte_formation=form.cleaned_data['ways_to_find_out_about_the_course'],
                    autre_moyen_decouverte_formation=form.cleaned_data['other_way_to_find_out_about_the_course'],
                    marque_d_interet=form.cleaned_data['interested_mark'],
                )
            )

        elif self.is_doctorate:
            message_bus_instance.invoke(
                ModifierChoixFormationDoctoraleParGestionnaireCommand(
                    uuid_proposition=self.admission_uuid,
                    auteur=self.request.user.person.global_id,
                    type_admission=form.cleaned_data['admission_type'],
                    commission_proximite=form.cleaned_data.get(form.proximity_commission_field, ''),
                    justification=form.cleaned_data['justification'],
                    reponses_questions_specifiques=form.cleaned_data['specific_question_answers'],
                )
            )

        return super().form_valid(form)

    def get_success_url(self):
        return self.next_url or reverse(f'admission:{self.current_context}:training-choice', kwargs=self.kwargs)
