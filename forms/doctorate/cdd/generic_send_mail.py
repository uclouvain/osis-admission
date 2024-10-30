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
from ckeditor.fields import RichTextFormField
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.models import CddMailTemplate


class SelectCddEmailTemplateForm(forms.Form):
    template = forms.ChoiceField(
        label=_("Select a mail template"),
        widget=forms.Select(
            attrs={
                "hx-get": "",
                "hx-target": "#sendmail-form-content",
                "hx-indicator": "#htmx-overlay",
            }
        ),
        required=True,
    )

    def __init__(self, identifier, admission, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['template'].choices = self.get_mail_template_choices(
            identifier,
            admission.candidate.language,
            admission.doctorate.management_entity_id,
        )

        self.fields['template'].initial = self.initial.get('template')

        if len(self.fields['template'].choices) <= 1:
            self.fields['template'].widget = forms.HiddenInput()

    @classmethod
    def get_mail_template_choices(cls, identifier, language, cdd_id):
        custom_templates = CddMailTemplate.objects.get_from_identifiers(
            identifiers=[identifier],
            language=language,
            cdd_id=cdd_id,
        )

        choices = [(identifier, _('Generic'))] + [
            (custom_template.pk, custom_template.name) for custom_template in custom_templates
        ]

        return choices


class BaseEmailTemplateForm(forms.Form):
    subject = forms.CharField(
        label=_("Message subject"),
    )
    body = RichTextFormField(
        label=_("Message body"),
        config_name='osis_mail_template',
    )
