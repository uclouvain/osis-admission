# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import forms
from django.utils.translation import gettext_lazy as _


class NameMailTemplateForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=255)
    cdd = forms.ChoiceField(label=_('CDD'))

    def __init__(self, cdds=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['cdd'].choices = [
            (cdd.id, f"{cdd.most_recent_acronym} - {cdd.most_recent_entity_version.title}") for cdd in cdds
        ]
