# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from collections import defaultdict

from ckeditor.fields import RichTextFormField
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.models import CddMailTemplate, DoctorateAdmission
from admission.utils import get_mail_templates_from_admission
from base.forms.utils import EMPTY_CHOICE


class CddDoctorateSendMailForm(forms.Form):
    recipient = forms.CharField(
        label=_("Recipient"),
        disabled=True,
    )
    template = forms.ChoiceField(
        label=_("Select a mail template"),
        widget=forms.Select(
            attrs={
                "hx-get": "",
                "hx-target": "#sendmail-form-content",
                "hx-indicator": "#htmx-overlay",
                "hx-include": "[name=cc_promoteurs],[name=cc_membres_ca]",
            }
        ),
        required=False,
    )
    cc_promoteurs = forms.BooleanField(
        label=_("Carbon-copy the promoters"),
        required=False,
    )
    cc_membres_ca = forms.BooleanField(
        label=_("Carbon-copy the CA members"),
        required=False,
    )
    subject = forms.CharField(
        label=_("Message subject"),
    )
    body = RichTextFormField(
        label=_("Message for the candidate"),
        config_name='osis_mail_template',
    )

    def __init__(self, admission: 'DoctorateAdmission', *args, **kwargs):
        self.admission = admission
        super().__init__(*args, **kwargs)
        self.fields['recipient'].initial = '{candidate.first_name} {candidate.last_name} ({candidate.email})'.format(
            candidate=self.admission.candidate,
        )
        self.fields['template'].choices = self.get_mail_template_choices()

    def get_mail_template_choices(self):
        from osis_mail_template import templates

        available_identifiers = get_mail_templates_from_admission(self.admission)
        custom_templates = CddMailTemplate.objects.get_from_identifiers(
            identifiers=available_identifiers,
            language=self.admission.candidate.language,
            cdd_id=self.admission.doctorate.management_entity_id,
        )

        # Regroup custom templates by their identifier and format into choices
        grouped_custom = defaultdict(list)
        for custom_template in custom_templates:
            grouped_custom[custom_template.identifier].append(
                (custom_template.pk, custom_template.name),
            )

        choices = list(EMPTY_CHOICE)
        for identifier in available_identifiers:
            if grouped_custom[identifier]:
                # Add a choice group with generic and custom templates
                choices.append((templates.get_description(identifier), grouped_custom[identifier]))
            else:
                # Add a simple choice
                choices.append((identifier, templates.get_description(identifier)))
        return choices
