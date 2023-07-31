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
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixLangueRedactionThese
from admission.ddd.parcours_doctoral.jury.domain.model.enums import FormuleDefense
from admission.forms import CustomDateInput


class JuryPreparationForm(forms.Form):
    titre_propose = forms.CharField(
        label=_("Proposed thesis title"),
        help_text=_("This is a temporary title and it will be modifiable later depending on the jury analysis."),
        required=False,
    )
    formule_defense = forms.ChoiceField(
        label=_("Defense method"),
        help_text=_(
            "Refer to the specific measures of your doctoral commission to know if one of these method is "
            "mandatory to you."
        ),
        choices=FormuleDefense.choices(),
        widget=forms.RadioSelect(),
        initial=FormuleDefense.FORMULE_1.name,
        required=False,
    )
    date_indicative = forms.DateField(
        label=_("Defense indicative date"),
        required=False,
        widget=CustomDateInput(),
    )
    langue_redaction = forms.ChoiceField(
        label=_("Thesis redacting language"),
        choices=ChoixLangueRedactionThese.choices(),
        initial=ChoixLangueRedactionThese.UNDECIDED.name,
        required=True,
    )
    langue_soutenance = forms.ChoiceField(
        label=_("Defense language"),
        choices=ChoixLangueRedactionThese.choices(),
        initial=ChoixLangueRedactionThese.UNDECIDED.name,
        required=False,
    )
    commentaire = forms.CharField(
        label=_("Comment"),
        widget=forms.Textarea(),
        required=False,
    )
