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
from dal import autocomplete
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.contrib.models import Scholarship
from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.enums import TypeBourse
from admission.ddd.admission.formation_generale.dtos.proposition import PropositionGestionnaireDTO
from admission.forms import RadioBooleanField, get_scholarship_choices, format_training
from admission.forms.specific_question import ConfigurableFormMixin
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE


class TrainingChoiceForm(ConfigurableFormMixin):
    training_type = forms.ChoiceField(
        choices=TypeFormation.choices(),
        label=_('Course type'),
        disabled=True,
        required=False,
    )

    campus = forms.ChoiceField(
        label=_('Campus (optional)'),
        disabled=True,
        required=False,
    )

    general_education_training = forms.ChoiceField(
        label=pgettext_lazy('admission', 'Course'),
        disabled=True,
        required=False,
    )

    has_double_degree_scholarship = RadioBooleanField(
        label=_('Are you a dual degree student?'),
        required=False,
        help_text=_(
            'Dual degrees involve joint coursework between two or more universities, leading to two separate diplomas '
            'awarded by each signatory university.'
        ),
    )

    double_degree_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2,
    )

    has_international_scholarship = RadioBooleanField(
        label=_('Do you have an international scholarship?'),
        required=False,
        help_text=_(
            'An international scholarship may be awarded to students as part of a project. These international '
            'grants are awarded by ARES and a scholarship certificate must be provided.'
        ),
    )

    international_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2,
    )

    has_erasmus_mundus_scholarship = RadioBooleanField(
        label=_('Are you an Erasmus Mundus student?'),
        required=False,
        help_text=_(
            'Erasmus Mundus is a study abroad programme devised by an international partnership of higher '
            'education institutions. Scholarships are awarded to students and proof of funding is therefore required.'
        ),
    )

    erasmus_mundus_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2,
    )

    def __init__(self, proposition: PropositionGestionnaireDTO, *args, **kwargs):
        self.training_type = AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE[
            proposition.formation.type
        ]

        kwargs['initial'] = {
            'campus': proposition.formation.campus.nom if proposition.formation.campus else '',
            'training_type': self.training_type,
            'double_degree_scholarship': proposition.bourse_double_diplome and proposition.bourse_double_diplome.uuid,
            'international_scholarship': proposition.bourse_internationale and proposition.bourse_internationale.uuid,
            'erasmus_mundus_scholarship': proposition.bourse_erasmus_mundus and proposition.bourse_erasmus_mundus.uuid,
            'general_education_training': proposition.formation.sigle,
            'specific_question_answers': proposition.reponses_questions_specifiques,
        }

        super().__init__(*args, **kwargs)

        # Initialize fields choices
        self.fields['campus'].choices = [[self.initial['campus'], self.initial['campus']]]

        self.fields['general_education_training'].choices = [
            [self.initial['general_education_training'], mark_safe(format_training(proposition.formation))]
        ]

        scholarships = (
            Scholarship.objects.filter(disabled=False).order_by('long_name', 'short_name')
            if self.training_type == TypeFormation.MASTER.name
            else []
        )

        self.scholarship_fields = [
            ['double_degree_scholarship', TypeBourse.DOUBLE_TRIPLE_DIPLOMATION],
            ['international_scholarship', TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE],
            ['erasmus_mundus_scholarship', TypeBourse.ERASMUS_MUNDUS],
        ]

        for scholarship_field, scholarship_type in self.scholarship_fields:
            self.initial[f'has_{scholarship_field}'] = bool(self.initial.get(scholarship_field))
            self.fields[scholarship_field].choices = get_scholarship_choices(
                scholarships=scholarships,
                scholarship_type=scholarship_type,
            )
            self.fields[scholarship_field].widget.choices = self.fields[scholarship_field].choices

    def clean(self):
        cleaned_data = super().clean()
        self.clean_master_scholarships(cleaned_data)
        return cleaned_data

    def clean_master_scholarships(self, cleaned_data):
        if self.training_type == TypeFormation.MASTER.name:
            for scholarship_field, _ in self.scholarship_fields:
                if cleaned_data.get(f'has_{scholarship_field}'):
                    if not cleaned_data.get(scholarship_field):
                        self.add_error(scholarship_field, FIELD_REQUIRED_MESSAGE)
                else:
                    cleaned_data[scholarship_field] = ''

                    if cleaned_data.get(f'has_{scholarship_field}') is None:
                        self.add_error(f'has_{scholarship_field}', FIELD_REQUIRED_MESSAGE)

        else:
            for scholarship_field, _ in self.scholarship_fields:
                cleaned_data[scholarship_field] = ''
                cleaned_data[f'has_{scholarship_field}'] = ''

    class Media:
        js = ('js/dependsOn.min.js',)
