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
from typing import List

from ckeditor.fields import RichTextFormField
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, get_language

from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument, TypeEmplacementDocument
from admission.forms import AdmissionFileUploadField, CustomDateInput
from admission.templatetags.admission import formatted_language


class UploadFreeDocumentForm(forms.Form):
    file_name = forms.CharField(
        label=_('File name'),
    )

    file = AdmissionFileUploadField(
        label=_('File'),
        max_files=1,
        min_files=1,
    )


class RequestFreeDocumentForm(forms.Form):
    file_name = forms.CharField(
        label=_('File name'),
    )

    reason = forms.CharField(
        label=_('Reason'),
        widget=forms.Textarea,
    )


class RequestDocumentForm(forms.Form):
    is_requested = forms.BooleanField(
        label=_('Document to be requested'),
        required=False,
    )

    reason = forms.CharField(
        widget=forms.Textarea,
    )

    def __init__(self, candidate_language, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reason'].label = mark_safe(
            _('Communication to the candidate, in <span class="label label-admission-primary">%s</span>')
            % formatted_language(candidate_language)
        )
        self.fields['reason'].required = bool(
            self.data.get(
                self.add_prefix('is_requested'),
                True,
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('is_requested'):
            cleaned_data['reason'] = ''

        return cleaned_data


class RequestAllDocumentsForm(forms.Form):
    deadline = forms.DateField(
        label=_('Deadline'),
        widget=CustomDateInput(),
    )

    documents = forms.MultipleChoiceField(
        label=_('Documents to be requested now'),
        widget=forms.CheckboxSelectMultiple,
    )

    message_object = forms.CharField(
        label=_('Message object'),
    )

    message_content = RichTextFormField(
        label=_('Message for the candidate'),
        config_name='link_only',
    )

    def __init__(self, documents: List[EmplacementDocumentDTO], *args, **kwargs):
        super().__init__(*args, **kwargs)

        documents_choices = []
        initial_document_choices = []

        self.fields['message_content'].widget.config['extraAllowedContent'] = 'span(*)[*]{*};ul(*)[*]{*}'
        self.fields['message_content'].widget.config['language'] = get_language()

        for document in documents:
            if document.statut == StatutEmplacementDocument.A_RECLAMER.name:
                if document.document_uuids:
                    label = '<span class="fa-solid fa-paperclip"></span> '
                else:
                    label = '<span class="fa-solid fa-link-slash"></span> '
                if document.type == TypeEmplacementDocument.LIBRE_CANDIDAT_FAC.name:
                    label += '<i class="fa-solid fa-building-columns"/> '
                label += document.libelle

                initial_document_choices.append(document.identifiant)
                documents_choices.append((document.identifiant, mark_safe(label)))

        self.fields['documents'].choices = documents_choices
        self.fields['documents'].initial = initial_document_choices

    class Media:
        js = [
            'js/moment.min.js',
            'js/locales/moment-fr.js',
        ]
