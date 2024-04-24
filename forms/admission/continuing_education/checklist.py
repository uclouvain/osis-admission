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
import json

from django import forms
from django.conf import settings
from django.utils.translation import (
    gettext_lazy as _,
    get_language,
    override,
)

from admission.contrib.models import ContinuingEducationAdmission
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixMotifRefus, ChoixMotifAttente
from admission.forms import CKEDITOR_MAIL_EXTRA_ALLOWED_CONTENT
from base.models.utils.utils import ChoiceEnum


class StudentReportForm(forms.ModelForm):
    class Meta:
        model = ContinuingEducationAdmission
        fields = [
            'interested_mark',
            'edition',
            'in_payement_order',
            'reduced_rights',
            'pay_by_training_cheque',
            'cep',
            'payement_spread',
            'training_spread',
            'experience_knowledge_valorisation',
            'assessment_test_presented',
            'assessment_test_succeeded',
            'certificate_provided',
            'tff_label',
        ]
        widgets = {
            'interested_mark': forms.CheckboxInput(),
            'in_payement_order': forms.CheckboxInput(),
            'reduced_rights': forms.CheckboxInput(),
            'pay_by_training_cheque': forms.CheckboxInput(),
            'cep': forms.CheckboxInput(),
            'payement_spread': forms.CheckboxInput(),
            'training_spread': forms.CheckboxInput(),
            'experience_knowledge_valorisation': forms.CheckboxInput(),
            'assessment_test_presented': forms.CheckboxInput(),
            'assessment_test_succeeded': forms.CheckboxInput(),
            'certificate_provided': forms.CheckboxInput(),
            'tff_label': forms.TextInput(),
        }


class DecisionFacApprovalChoices(ChoiceEnum):
    AVEC_CONDITION = _('With condition')
    SANS_CONDITION = _('Without condition')


class DecisionFacApprovalForm(forms.Form):
    accepter_la_demande = forms.ChoiceField(
        choices=DecisionFacApprovalChoices.choices(),
        required=True,
        initial=DecisionFacApprovalChoices.SANS_CONDITION.name,
        widget=forms.RadioSelect(),
    )

    condition_acceptation = forms.CharField(
        label=_('Acceptation condition'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )

    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = forms.CharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(
            attrs={
                'data-config': json.dumps(
                    {
                        **settings.CKEDITOR_CONFIGS['link_only'],
                        'extraAllowedContent': CKEDITOR_MAIL_EXTRA_ALLOWED_CONTENT,
                        'language': get_language(),
                    }
                )
            }
        ),
    )

    class Media:
        js = [
            'js/dependsOn.min.js',
        ]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data[
            'accepter_la_demande'
        ] == DecisionFacApprovalChoices.AVEC_CONDITION.name and not cleaned_data.get('condition_acceptation'):
            self.add_error(
                'condition_acceptation',
                forms.ValidationError(
                    self.fields['condition_acceptation'].error_messages['required'],
                    code='required',
                ),
            )
        return cleaned_data


class DecisionDenyForm(forms.Form):
    reason = forms.ChoiceField(
        label=_('Refusal reason'),
        choices=ChoixMotifRefus.choices(),
        required=True,
    )

    other_reason = forms.CharField(
        label=_('Other refusal reason'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )

    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = forms.CharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(
            attrs={
                'data-config': json.dumps(
                    {
                        **settings.CKEDITOR_CONFIGS['link_only'],
                        'extraAllowedContent': CKEDITOR_MAIL_EXTRA_ALLOWED_CONTENT,
                        'language': get_language(),
                    }
                )
            }
        ),
    )

    class Media:
        js = [
            'js/dependsOn.min.js',
        ]

    def __init__(self, candidate_language, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with override(candidate_language):
            self.translated_reasons = {choice[0]: str(choice[1]) for choice in self.fields['reason'].choices}

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['reason'] == ChoixMotifRefus.AUTRE.name and not cleaned_data.get('other_reason'):
            self.add_error(
                'other_reason',
                forms.ValidationError(
                    self.fields['other_reason'].error_messages['required'],
                    code='required',
                ),
            )
        return cleaned_data


class DecisionHoldForm(forms.Form):
    reason = forms.ChoiceField(
        label=_('Holding reason'),
        choices=ChoixMotifAttente.choices(),
        required=True,
    )

    other_reason = forms.CharField(
        label=_('Other holding reason'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )

    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = forms.CharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(
            attrs={
                'data-config': json.dumps(
                    {
                        **settings.CKEDITOR_CONFIGS['link_only'],
                        'extraAllowedContent': CKEDITOR_MAIL_EXTRA_ALLOWED_CONTENT,
                        'language': get_language(),
                    }
                )
            }
        ),
    )

    class Media:
        js = [
            'js/dependsOn.min.js',
        ]

    def __init__(self, candidate_language, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with override(candidate_language):
            self.translated_reasons = {choice[0]: str(choice[1]) for choice in self.fields['reason'].choices}

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['reason'] == ChoixMotifAttente.AUTRE.name and not cleaned_data.get('other_reason'):
            self.add_error(
                'other_reason',
                forms.ValidationError(
                    self.fields['other_reason'].error_messages['required'],
                    code='required',
                ),
            )
        return cleaned_data


class DecisionCancelForm(forms.Form):
    reason = forms.CharField(
        label=_('Reason for cancellation'),
        widget=forms.Textarea(attrs={'rows': 2}),
        required=True,
    )

    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = forms.CharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(
            attrs={
                'data-config': json.dumps(
                    {
                        **settings.CKEDITOR_CONFIGS['link_only'],
                        'extraAllowedContent': CKEDITOR_MAIL_EXTRA_ALLOWED_CONTENT,
                        'language': get_language(),
                    }
                )
            }
        ),
    )

    class Media:
        js = [
            'js/dependsOn.min.js',
        ]


class DecisionValidationForm(forms.Form):
    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = forms.CharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(
            attrs={
                'data-config': json.dumps(
                    {
                        **settings.CKEDITOR_CONFIGS['link_only'],
                        'extraAllowedContent': CKEDITOR_MAIL_EXTRA_ALLOWED_CONTENT,
                        'language': get_language(),
                    }
                )
            }
        ),
    )


class CloseForm(forms.Form):
    pass


class SendToFacForm(forms.Form):
    comment = forms.CharField(
        label=_('Comment'),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True,
    )

    subject = forms.CharField(
        label=_('Message subject'),
    )
    body = forms.CharField(
        label=_('Message for the faculty'),
        widget=forms.Textarea(
            attrs={
                'data-config': json.dumps(
                    {
                        **settings.CKEDITOR_CONFIGS['link_only'],
                        'extraAllowedContent': CKEDITOR_MAIL_EXTRA_ALLOWED_CONTENT,
                        'language': get_language(),
                    }
                )
            }
        ),
    )
