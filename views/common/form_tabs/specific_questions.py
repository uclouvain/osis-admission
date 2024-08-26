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
from attr import asdict
from django.urls import reverse
from django.views.generic import FormView

from admission.ddd.admission.formation_continue.commands import (
    CompleterQuestionsSpecifiquesParGestionnaireCommand as CompleterQuestionsSpecifiquesContinuesParGestionnaireCommand,
)
from admission.ddd.admission.formation_generale.commands import (
    CompleterQuestionsSpecifiquesParGestionnaireCommand as CompleterQuestionsSpecifiquesGeneralesParGestionnaireCommand,
)
from admission.forms.admission.specific_questions import GeneralSpecificQuestionsForm, ContinuingSpecificQuestionsForm
from admission.constants import CONTEXT_GENERAL, CONTEXT_CONTINUING
from admission.views.common.detail_tabs.specific_questions import SpecificQuestionsMixinView
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'SpecificQuestionsFormView',
]

from osis_profile import BE_ISO_CODE


class SpecificQuestionsFormView(SpecificQuestionsMixinView, FormView):
    permission_required = 'admission.change_admission_specific_questions'
    urlpatterns = 'specific-questions'

    def get_template_names(self):
        return [
            {
                CONTEXT_GENERAL: 'admission/general_education/forms/specific_questions.html',
                CONTEXT_CONTINUING: 'admission/continuing_education/forms/specific_questions.html',
            }[self.current_context]
        ]

    def get_form_class(self):
        return {
            CONTEXT_GENERAL: GeneralSpecificQuestionsForm,
            CONTEXT_CONTINUING: ContinuingSpecificQuestionsForm,
        }[self.current_context]

    def get_initial(self):
        initial_data = asdict(self.proposition)

        if self.is_general:
            initial_data['poste_diplomatique'] = (
                self.proposition.poste_diplomatique.code if self.proposition.poste_diplomatique else None
            )
        elif self.is_continuing:
            adresse_facturation = initial_data.pop('adresse_facturation', {})
            if adresse_facturation:
                initial_data.update(
                    {
                        'adresse_facturation_destinataire': adresse_facturation.get('destinataire'),
                        'street': adresse_facturation.get('rue'),
                        'street_number': adresse_facturation.get('numero_rue'),
                        'postal_box': adresse_facturation.get('boite_postale'),
                        'postal_code': adresse_facturation.get('code_postal'),
                        'city': adresse_facturation.get('ville'),
                        'country': adresse_facturation.get('pays'),
                    }
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

        elif self.is_continuing:
            kwargs['display_residence_permit_question'] = self.display_residence_permit_question

        return kwargs

    def form_valid(self, form):
        if self.is_general:
            message_bus_instance.invoke(
                CompleterQuestionsSpecifiquesGeneralesParGestionnaireCommand(
                    uuid_proposition=self.proposition.uuid,
                    gestionnaire=self.request.user.person.global_id,
                    **form.cleaned_data,
                )
            )
        elif self.is_continuing:
            address_data = form.address_data_to_save
            message_bus_instance.invoke(
                CompleterQuestionsSpecifiquesContinuesParGestionnaireCommand(
                    uuid_proposition=self.proposition.uuid,
                    gestionnaire=self.request.user.person.global_id,
                    inscription_a_titre=form.cleaned_data['inscription_a_titre'],
                    reponses_questions_specifiques=form.cleaned_data['reponses_questions_specifiques'],
                    copie_titre_sejour=form.cleaned_data['copie_titre_sejour'],
                    documents_additionnels=form.cleaned_data['documents_additionnels'],
                    nom_siege_social=form.cleaned_data['nom_siege_social'],
                    numero_unique_entreprise=form.cleaned_data['numero_unique_entreprise'],
                    numero_tva_entreprise=form.cleaned_data['numero_tva_entreprise'],
                    adresse_mail_professionnelle=form.cleaned_data['adresse_mail_professionnelle'],
                    type_adresse_facturation=form.cleaned_data['type_adresse_facturation'],
                    adresse_facturation_rue=address_data['street'],
                    adresse_facturation_numero_rue=address_data['street_number'],
                    adresse_facturation_code_postal=address_data['postal_code'],
                    adresse_facturation_ville=address_data['city'],
                    adresse_facturation_pays=address_data['country'].iso_code if address_data['country'] else None,
                    adresse_facturation_destinataire=form.cleaned_data['adresse_facturation_destinataire'],
                    adresse_facturation_boite_postale=address_data['postal_box'],
                )
            )
        return super().form_valid(form)

    def get_success_url(self):
        return self.next_url or reverse(f'admission:{self.current_context}:specific-questions', kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['BE_ISO_CODE'] = BE_ISO_CODE
        return context
