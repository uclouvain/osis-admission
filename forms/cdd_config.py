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

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from admission.models.cdd_config import CddConfiguration
from admission.ddd.parcours_doctoral.formation.domain.model.enums import CategorieActivite


class CddConfigForm(forms.ModelForm):
    class Meta:
        model = CddConfiguration
        exclude = ['cdd', 'id']
        help_texts = {
            'category_labels': _("Do not reorder values, and keep the same count"),
        }

    def clean_category_labels(self):
        data = self.cleaned_data['category_labels']
        expected_length = len(CategorieActivite.choices())
        if any(len(data[lang]) != expected_length for lang in dict(settings.LANGUAGES)):
            raise ValidationError(_("Number of values mismatch"))
        return data
