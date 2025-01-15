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

from admission.models import DoctorateAdmission


class CddDoctorateSendMailForm(forms.Form):
    recipient = forms.CharField(
        label=_("Recipient"),
        disabled=True,
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
