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
import datetime

from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import PoursuiteDeCycle
from admission.forms import get_academic_year_choices
from base.models.academic_year import AcademicYear


class CommentForm(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 2,
                'hx-trigger': 'keyup changed delay:2s',
                'hx-target': 'closest .form-group',
                'hx-swap': 'outerHTML',
            }
        ),
        label=_("Comment"),
        required=False,
    )

    def __init__(self, form_url, comment=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].widget.attrs['hx-post'] = form_url
        if comment:
            self.fields['comment'].initial = comment.content
            self.fields['comment'].label += _(" (last update by {author} on {date} at {time}):").format(
                author=comment.author,
                date=comment.modified_at.strftime("%d/%m/%Y"),
                time=comment.modified_at.strftime("%H:%M"),
            )


class DateInput(forms.DateInput):
    input_type = 'date'


class AssimilationForm(forms.Form):
    date_debut = forms.DateField(
        widget=DateInput(
            attrs={
                'hx-trigger': 'change changed delay:2s',
                'hx-target': 'closest .form-group',
                'hx-validate': 'true',
                'hx-swap': 'outerHTML',
            },
        ),
        label=_("Assimilation start date"),
    )

    def __init__(self, form_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_debut'].widget.attrs['hx-post'] = form_url


class ChoixFormationForm(forms.Form):
    type_demande = forms.ChoiceField(
        label=_("Proposition type"),
        choices=TypeDemande.choices(),
    )
    annee_academique = forms.ChoiceField(
        label=_("Academic year"),
    )
    formation = forms.CharField(
        label=_("Training"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:general-education-trainings"),
    )
    poursuite_cycle = forms.ChoiceField(
        label=_("Cycle pursuit"),
        choices=PoursuiteDeCycle.choices(),
    )

    def __init__(self, *args, **kwargs):
        formation = kwargs.pop('formation')
        super().__init__(*args, **kwargs)
        today = datetime.date.today()
        try:
            current_year = AcademicYear.objects.get(start_date__lte=today, end_date__gt=today).year
        except AcademicYear.DoesNotExist:
            current_year = today.year
        self.fields['annee_academique'].choices = get_academic_year_choices(current_year - 2, current_year + 2)
        self.fields['formation'].widget.choices = [(formation.sigle, f'{formation.sigle} - {formation.intitule}')]
