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

from admission.contrib.models.doctoral_training import Activity


class BatchActivityForm(forms.Form):
    activity_ids = forms.ModelMultipleChoiceField(Activity.objects.none(), to_field_name='uuid')

    def __init__(self, doctorate_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['activity_ids'].queryset = Activity.objects.filter(doctorate_id=doctorate_id)

    def clean(self):
        data = super().clean()
        if not data.get('activity_ids'):
            self.add_error(None, _("Select at least one activity"))
        return data


class RefuseForm(forms.Form):
    reason = forms.CharField(label=_("Comment"), widget=forms.Textarea())
