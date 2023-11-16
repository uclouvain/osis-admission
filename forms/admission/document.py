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
import json
from typing import List

from django import forms
from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, get_language, pgettext_lazy

from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import (
    StatutEmplacementDocument,
    TypeEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from admission.forms import AdmissionFileUploadField, CustomDateInput
from admission.templatetags.admission import formatted_language, document_request_status_css_class
from base.forms.utils.choice_field import BLANK_CHOICE


class UploadDocumentFormMixin(forms.Form):
    def __init__(self, mimetypes, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'] = AdmissionFileUploadField(
            label=_('File'),
            max_files=1,
            min_files=1,
            mimetypes=mimetypes,
        )


class ReplaceDocumentForm(UploadDocumentFormMixin):
    pass


class UploadDocumentForm(UploadDocumentFormMixin):
    pass


class UploadFreeDocumentForm(forms.Form):
    file_name = forms.CharField(
        label=pgettext_lazy('admission', 'File name'),
    )

    file = AdmissionFileUploadField(
        label=_('File'),
        max_files=1,
        min_files=1,
    )


REQUEST_STATUS_CHOICES = StatutReclamationEmplacementDocument.choices()
REQUEST_STATUS_CHOICES_WITH_OPTIONAL = (BLANK_CHOICE[0],) + StatutReclamationEmplacementDocument.choices()


class RequestFreeDocumentForm(forms.Form):
    file_name = forms.CharField(
        label=pgettext_lazy('admission', 'File name'),
    )

    reason = forms.CharField(
        label=pgettext_lazy('admission', 'Reason'),
        widget=forms.Textarea,
        required=False,
    )

    request_status = forms.ChoiceField(
        label=_('Document to be requested'),
        choices=REQUEST_STATUS_CHOICES_WITH_OPTIONAL,
    )


class RequestFreeDocumentWithDefaultFileForm(UploadFreeDocumentForm):
    pass


class ChangeRequestDocumentForm(forms.Form):
    @classmethod
    def create_change_request_document_field(
        cls,
        label,
        request_status,
        document_identifier,
        proposition_uuid,
        automatically_required,
    ):
        document_field = forms.ChoiceField(
            label=label,
            required=automatically_required,
            choices=REQUEST_STATUS_CHOICES if automatically_required else REQUEST_STATUS_CHOICES_WITH_OPTIONAL,
            initial=request_status,
        )
        document_field.widget.attrs['hx-trigger'] = 'change changed delay:2s, confirmStatusChange'
        document_field.widget.attrs['hx-swap'] = 'none'
        document_field.widget.attrs['hx-target'] = 'this'
        document_field.widget.attrs['hx-post'] = resolve_url(
            'admission:general-education:document:candidate-request-status',
            uuid=proposition_uuid,
            identifier=document_identifier,
        )
        return document_field

    def __init__(self, document_identifier, proposition_uuid, automatically_required, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[document_identifier] = self.create_change_request_document_field(
            label='',
            request_status='',
            document_identifier=document_identifier,
            proposition_uuid=proposition_uuid,
            automatically_required=automatically_required,
        )


class RequestDocumentForm(forms.Form):
    request_status = forms.ChoiceField(
        label=_('Document to be requested'),
        required=False,
        choices=[],
    )

    reason = forms.CharField(
        widget=forms.Textarea,
        required=False,
    )

    def __init__(self, candidate_language, auto_requested=False, editable_document=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['reason'].label = mark_safe(
            _(
                'Communication to the candidate, in <span class="label label-admission-primary">{language_code}]</span>'
            ).format(language_code=formatted_language(candidate_language))
        )

        request_status = self.data.get('request_status', self.initial.get('request_status'))
        if request_status:
            self.fields['request_status'].label = mark_safe(
                f'{self.fields["request_status"].label} '
                f'<span class="fa-solid fa-file {document_request_status_css_class(request_status)}"></span>'
            )

        self.auto_requested = auto_requested
        self.fields['request_status'].choices = (
            REQUEST_STATUS_CHOICES if auto_requested else REQUEST_STATUS_CHOICES_WITH_OPTIONAL
        )
        if auto_requested:
            # If the document is automatically requested, it must be requested to specify a reason
            self.fields['request_status'].required = True
            self.fields['request_status'].widget.attrs['title'] = _('Automatically required')

        if not editable_document:
            self.fields['request_status'].disabled = True
            self.fields['reason'].disabled = True

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('request_status'):
            cleaned_data['reason'] = ''

        return cleaned_data


class RequestAllDocumentsForm(forms.Form):
    deadline = forms.DateField(
        label=_('Deadline for documents to be requested immediately'),
        widget=CustomDateInput(),
    )

    message_object = forms.CharField(
        label=_('Message object'),
    )

    message_content = forms.CharField(
        label=_('Message for the candidate'),
        widget=forms.Textarea(),
    )

    def __init__(self, documents: List[EmplacementDocumentDTO], proposition_uuid, *args, **kwargs):
        super().__init__(*args, **kwargs)

        documents_choices = []
        initial_document_choices = []

        self.fields['message_content'].widget.attrs['data-config'] = json.dumps(
            {
                **settings.CKEDITOR_CONFIGS['link_only'],
                'extraAllowedContent': 'span(*)[*]{*};ul(*)[*]{*}',
                'language': get_language(),
            }
        )

        self.documents = {}

        for document in documents:
            if document.statut == StatutEmplacementDocument.A_RECLAMER.name:
                if document.document_uuids:
                    label = '<span class="fa-solid fa-paperclip"></span> '
                else:
                    label = '<span class="fa-solid fa-link-slash"></span> '
                if document.type == TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name:
                    label += '<span class="fa-solid fa-building-columns"></span> '
                label += document.libelle

                document_field = ChangeRequestDocumentForm.create_change_request_document_field(
                    label=label,
                    document_identifier=document.identifiant,
                    request_status=document.statut_reclamation,
                    proposition_uuid=proposition_uuid,
                    automatically_required=document.requis_automatiquement,
                )

                self.fields[document.identifiant] = document_field
                self.documents[document.identifiant] = document_field

                initial_document_choices.append(document.identifiant)
                documents_choices.append((document.identifiant, mark_safe(label)))

    class Media:
        js = [
            'js/moment.min.js',
            'js/locales/moment-fr.js',
        ]

    def clean(self):
        cleaned_data = super().clean()

        # Merge the contents of the documents fields
        requested_documents = []

        for field_name in self.documents:
            if self.cleaned_data.get(field_name):
                requested_documents.append(field_name)

        if not requested_documents:
            self.add_error(None, _('At least one document must be selected.'))

        cleaned_data['requested_documents'] = requested_documents

        return cleaned_data
