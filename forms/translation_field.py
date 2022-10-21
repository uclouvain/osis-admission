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
from typing import Any

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

TRANSLATION_LANGUAGES = [settings.LANGUAGE_CODE_EN, settings.LANGUAGE_CODE_FR]


class TranslatedValueWidget(forms.MultiWidget):
    """Widget of two textareas (one for each language)"""

    template_name = 'admission/config/translated_value_widget.html'

    def __init__(self, *args, **kwargs):
        widgets = {
            settings.LANGUAGE_CODE_EN: forms.Textarea(attrs={'placeholder': _("English value"), 'rows': 3}),
            settings.LANGUAGE_CODE_FR: forms.Textarea(attrs={'placeholder': _("French value"), 'rows': 3}),
        }
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        # On display, return an array of values

        if not value:
            return []

        return [value.get(language, '') for language in TRANSLATION_LANGUAGES]


class TranslatedValueField(forms.MultiValueField):
    widget = TranslatedValueWidget

    def __init__(self, *args, **kwargs):
        # Remove arguments from JSONField
        kwargs.pop("encoder", None)
        kwargs.pop("decoder", None)
        super().__init__((forms.CharField(), forms.CharField()), *args, **kwargs)

    def compress(self, data_list) -> Any:
        # On save, build a dict as JSON value
        if not data_list:
            return {}

        return {language: data_list[index] for index, language in enumerate(TRANSLATION_LANGUAGES)}
