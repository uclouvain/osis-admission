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
import datetime
import json

from django import forms
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    COMMISSIONS_CDE_CLSM,
    COMMISSIONS_CDSS,
    SIGLES_SCIENCES,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixSousDomaineSciences,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
)
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.forms import get_academic_year_choices
from base.models.academic_year import AcademicYear


class ProjetRechercheDemanderModificationCAForm(forms.Form):
    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = forms.CharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs['data-config'] = json.dumps(
            {
                **settings.CKEDITOR_CONFIGS['osis_mail_template'],
                'language': get_language(),
            }
        )


class ChoixFormationForm(forms.Form):
    type_demande = forms.ChoiceField(
        label=_('Proposition type'),
        choices=TypeDemande.choices(),
    )
    annee_academique = forms.ChoiceField(
        label=_('Academic year'),
    )
    commission_proximite = forms.ChoiceField(
        label=_('Proximity commission / Subdomain'),
    )

    @classmethod
    def get_proximity_commission_choices(cls, training: FormationDTO):
        if training.sigle_entite_gestion in COMMISSIONS_CDE_CLSM:
            return ChoixCommissionProximiteCDEouCLSM.choices()
        elif training.sigle_entite_gestion in COMMISSIONS_CDSS:
            return ChoixCommissionProximiteCDSS.choices()
        elif training.sigle in SIGLES_SCIENCES:
            return ChoixSousDomaineSciences.choices()
        return []

    def __init__(self, training, hide_admission_type=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = datetime.date.today()

        try:
            current_year = AcademicYear.objects.get(start_date__lte=today, end_date__gt=today).year
        except AcademicYear.DoesNotExist:
            current_year = today.year

        self.fields['annee_academique'].choices = get_academic_year_choices(current_year - 2, current_year + 2)

        self.fields['commission_proximite'].choices = self.get_proximity_commission_choices(training)

        if len(self.fields['commission_proximite'].choices) == 0:
            self.fields['commission_proximite'].required = False
            self.fields['commission_proximite'].disabled = True
            self.fields['commission_proximite'].widget = forms.HiddenInput()

        if hide_admission_type:
            self.fields['type_demande'].disabled = True
            self.fields['type_demande'].widget = forms.HiddenInput()
