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
import json
from typing import List, Optional

from dal import forward
from django import forms
from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, get_language, pgettext_lazy

from admission.contrib.models.categorized_free_document import CategorizedFreeDocument, TOKEN_ACADEMIC_YEAR
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import (
    StatutEmplacementDocument,
    TypeEmplacementDocument,
    StatutReclamationEmplacementDocument,
    DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION,
    STATUTS_EMPLACEMENT_DOCUMENT_A_RECLAMER,
)
from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist
from admission.forms import (
    OTHER_EMPTY_CHOICE,
    autocomplete,
    get_year_choices,
)
from admission.templatetags.admission import formatted_language, document_request_status_css_class
from admission.views.autocomplete.categorized_free_documents import CategorizedFreeDocumentsAutocomplete
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.choice_field import BLANK_CHOICE
from base.forms.utils.datefield import CustomDateInput
from base.forms.utils.file_field import MaxOneFileUploadField
from base.models.academic_year import AcademicYear


class UploadDocumentFormMixin(forms.Form):
    def __init__(self, mimetypes, identifier, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'] = MaxOneFileUploadField(
            label=_('File'),
            max_files=1,
            min_files=1,
            forced_mimetypes=mimetypes if identifier in DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION else None,
        )


class ReplaceDocumentForm(UploadDocumentFormMixin):
    pass


class UploadDocumentForm(UploadDocumentFormMixin):
    pass


class UploadFreeDocumentForm(forms.Form):
    file_name = forms.CharField(
        label=pgettext_lazy('admission', 'Document name'),
    )

    file = MaxOneFileUploadField(
        label=_('File'),
        max_files=1,
        min_files=1,
    )


REQUEST_STATUS_CHOICES = (BLANK_CHOICE[0],) + StatutReclamationEmplacementDocument.choices()
LIMITED_REQUEST_STATUS_CHOICES = (BLANK_CHOICE[0],) + StatutReclamationEmplacementDocument.choices_except(
    StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT,
    StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT,
)


def get_request_status_choices(only_limited_request_choices):
    return LIMITED_REQUEST_STATUS_CHOICES if only_limited_request_choices else REQUEST_STATUS_CHOICES


class FreeDocumentHelperFormMixin(forms.Form):
    checklist_tab = forms.ChoiceField(
        label=pgettext_lazy('admission', 'Checklist'),
        choices=OTHER_EMPTY_CHOICE + OngletsChecklist.choices_except(OngletsChecklist.experiences_parcours_anterieur),
        required=False,
    )

    document_type = forms.ModelChoiceField(
        label=pgettext_lazy('admission', 'Document type'),
        queryset=CategorizedFreeDocument.objects.all(),
        empty_label=_('Other'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:categorized-free-documents',
            forward=[forward.Field('checklist_tab', 'checklist_tab')],
            attrs={
                'data-placeholder': _('Other'),
                'data-allow-clear': 'true',
            },
        ),
    )

    academic_year = forms.ChoiceField(
        label=pgettext_lazy('admission', 'Academic year'),
        choices=OTHER_EMPTY_CHOICE,
        required=False,
    )

    def __init__(self, candidate_language, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tokens = {
            'academic_year': TOKEN_ACADEMIC_YEAR,
        }

        current_academic_year = AcademicYear.objects.current()

        self.candidate_language = candidate_language

        self.fields['academic_year'].choices = get_year_choices(
            min_year=current_academic_year.year - 100,
            max_year=current_academic_year.year,
            full_format=True,
            empty_label=_('To be determined'),
        )

        self.fields['document_type'].widget.forward.append(forward.Const(self.candidate_language, 'language'))

    def clean_document_type(self):
        document_type: Optional[CategorizedFreeDocument] = self.cleaned_data.get('document_type')

        if document_type:
            short_label_field_name = CategorizedFreeDocumentsAutocomplete.get_short_label_field(get_language())
            long_label_field_name = CategorizedFreeDocumentsAutocomplete.get_long_label_field(self.candidate_language)

            self.fields['document_type'].widget.attrs['data-data'] = json.dumps(
                [
                    {
                        'id': document_type.pk,
                        'text': getattr(document_type, short_label_field_name),
                        'selected_text': getattr(document_type, short_label_field_name),
                        'with_academic_year': document_type.with_academic_year,
                        'full_text': getattr(document_type, long_label_field_name),
                    }
                ]
            )

        return document_type

    def clean(self):
        cleaned_data = super().clean()

        checklist_tab = cleaned_data.get('checklist_tab')
        document_type: Optional[CategorizedFreeDocument] = self.cleaned_data.get('document_type')
        academic_year = cleaned_data.get('academic_year')

        if document_type:
            if checklist_tab and document_type.checklist_tab != checklist_tab:
                self.add_error('checklist_tab', _('The document must be related to the specified checklist tab'))
            if document_type.with_academic_year and not academic_year:
                self.add_error('academic_year', FIELD_REQUIRED_MESSAGE)

        return cleaned_data


class UploadManagerDocumentForm(FreeDocumentHelperFormMixin, UploadFreeDocumentForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove the checklist tab field and pass a constant value ('') to the document type autocomplete view
        # to return the document type that are not related to a checklist tab (UCLouvain documents).
        del self.fields['checklist_tab']

        self.fields['document_type'].widget.forward = [
            forward.Const(self.candidate_language, 'language'),
            forward.Const('', 'checklist_tab'),
        ]


class RequestFreeDocumentForm(FreeDocumentHelperFormMixin, forms.Form):
    file_name = forms.CharField(
        label=pgettext_lazy('admission', 'Document name'),
    )

    reason = forms.CharField(
        label=pgettext_lazy('admission', 'Reason'),
        widget=forms.Textarea,
        required=False,
    )

    request_status = forms.ChoiceField(
        label=_('Document to be requested'),
        choices=REQUEST_STATUS_CHOICES,
    )

    def __init__(self, only_limited_request_choices, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['request_status'].choices = get_request_status_choices(only_limited_request_choices)

        if len(self.fields['request_status'].choices) == 2:
            # If there is only one not empty choice, hide the field and select the related value
            self.initial['request_status'] = self.fields['request_status'].choices[1][0]
            self.fields['request_status'].widget = forms.HiddenInput()


class RequestFreeDocumentWithDefaultFileForm(FreeDocumentHelperFormMixin, UploadFreeDocumentForm):
    pass


class ChangeRequestDocumentForm(forms.Form):
    @classmethod
    def create_change_request_document_field(
        cls,
        label,
        request_status,
        document_identifier,
        proposition_uuid,
        only_limited_request_choices,
    ):
        document_field = forms.ChoiceField(
            label=label,
            required=False,
            choices=get_request_status_choices(only_limited_request_choices),
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

    def __init__(
        self,
        document_identifier,
        proposition_uuid,
        only_limited_request_choices,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fields[document_identifier] = self.create_change_request_document_field(
            label='',
            request_status='',
            document_identifier=document_identifier,
            proposition_uuid=proposition_uuid,
            only_limited_request_choices=only_limited_request_choices,
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

    def __init__(
        self,
        candidate_language,
        editable_document=False,
        only_limited_request_choices=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.fields['reason'].label = mark_safe(
            _(
                'Communication to the candidate (refusal reason), in '
                '<span class="label label-admission-primary">{language_code}]</span>'
            ).format(language_code=formatted_language(candidate_language))
        )

        request_status = self.data.get('request_status', self.initial.get('request_status'))
        if request_status:
            self.fields['request_status'].label = mark_safe(
                f'{self.fields["request_status"].label} '
                f'<span class="fa-solid fa-file {document_request_status_css_class(request_status)}"></span>'
            )

        self.fields['request_status'].choices = get_request_status_choices(only_limited_request_choices)

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

    def __init__(
        self,
        documents: List[EmplacementDocumentDTO],
        proposition_uuid,
        only_limited_request_choices,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        documents_choices = []
        initial_document_choices = []

        self.fields['message_content'].widget.attrs['data-config'] = json.dumps(
            {
                **settings.CKEDITOR_CONFIGS['osis_mail_template'],
                'language': get_language(),
            }
        )

        self.documents = {}

        for document in documents:
            if document.statut in STATUTS_EMPLACEMENT_DOCUMENT_A_RECLAMER and document.statut_reclamation:
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
                    only_limited_request_choices=only_limited_request_choices,
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


class RetypeDocumentForm(forms.Form):
    identifier = forms.CharField(
        label=_('What is the new type of this document?'),
        widget=autocomplete.Select2(
            url="admission:autocomplete:document-types-swap",
            attrs={'data-html': True},
        ),
    )

    def __init__(self, admission_uuid, identifier, **kwargs):
        super().__init__(**kwargs)
        self.fields['identifier'].widget.forward = [
            forward.Const(str(admission_uuid), 'admission_uuid'),
            forward.Const(identifier, 'document_identifier'),
        ]
