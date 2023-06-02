# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from dal import autocomplete


from django import forms
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _


class ControllerForm(forms.Form):
    entite_code = forms.CharField(disabled=True, widget=forms.HiddenInput())

    matricule = forms.CharField(
        label=_('Lookup somebody'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:jury-members",
            attrs={
                'data-minimum-input-length': 3,
                'data-placeholder': _('Last name / First name / Global id'),
            },
        ),
    )


ControllersFormset = formset_factory(ControllerForm, extra=0)
