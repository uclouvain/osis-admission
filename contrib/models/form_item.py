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
from functools import partial
from os.path import dirname

import uuid as uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _, ngettext_lazy
from osis_document.utils import generate_filename

from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    TypeItemFormulaire,
    CleConfigurationItemFormulaire,
    TypeChampTexteFormulaire,
)

TRANSLATION_LANGUAGES = [settings.LANGUAGE_CODE_EN, settings.LANGUAGE_CODE_FR]
DEFAULT_MAX_NB_DOCUMENTS = 1


def is_valid_translated_json_field(value):
    if not isinstance(value, dict):
        raise ValidationError(_('Must be a dictionary.'))

    if value:
        for language in TRANSLATION_LANGUAGES:
            if language not in value or not isinstance(value.get(language), str):
                raise ValidationError(
                    _('This field must contain a translation for each of the following languages: %(languages)s.')
                    % {'languages': str(TRANSLATION_LANGUAGES)}
                )


TranslatedJSONField = partial(
    models.JSONField,
    default=dict,
    validators=[is_valid_translated_json_field],
)


class AdmissionFormItem(models.Model):
    """This model store the configuration of a dynamic form field."""
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    education = models.ForeignKey(
        on_delete=models.CASCADE,
        to="base.EducationGroupYear",
        verbose_name=_("Education"),
    )
    type = models.CharField(
        choices=TypeItemFormulaire.choices(),
        max_length=30,
    )
    weight = models.PositiveIntegerField(
        verbose_name=_("Weight"),
    )
    deleted = models.BooleanField(
        default=False,
        verbose_name=_('Soft deleted'),
    )
    internal_label = models.CharField(
        max_length=255,
        verbose_name=_('Internal label'),
    )
    required = models.BooleanField(
        default=False,
        verbose_name=_('Required'),
    )
    title = TranslatedJSONField(
        blank=True,
        verbose_name=_('Title'),
    )
    text = TranslatedJSONField(
        blank=True,
        verbose_name=_('Text'),
    )
    help_text = TranslatedJSONField(
        blank=True,
        verbose_name=_('Help text'),
    )
    config = models.JSONField(
        blank=True,
        default=dict,
    )

    class Meta:
        ordering = ['education', 'weight']
        verbose_name = _('Admission form item')
        verbose_name_plural = _('Admission form items')

    config_allowed_properties = {
        TypeItemFormulaire.TEXTE.name: {
            CleConfigurationItemFormulaire.TAILLE_TEXTE.name,
        },
        TypeItemFormulaire.MESSAGE.name: {
            CleConfigurationItemFormulaire.CLASSE_CSS.name,
        },
        TypeItemFormulaire.DOCUMENT.name: {
            CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name,
            CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name,
        },
    }

    valid_form_item_text_types = set(TypeChampTexteFormulaire.get_names())

    def clean(self):
        config_errors = []
        invalid_config_keys = [key for key in self.config if key not in self.config_allowed_properties[self.type]]

        if invalid_config_keys:
            config_errors.append(
                ngettext_lazy(
                    'Invalid property: %(config_params)s',
                    'Invalid properties: %(config_params)s',
                    len(invalid_config_keys),
                )
                % {'config_params': ','.join(invalid_config_keys)}
            )

        if self.type == TypeItemFormulaire.MESSAGE.name:
            self.required = False
            css_class = self.config.get(CleConfigurationItemFormulaire.CLASSE_CSS.name)
            if css_class is not None and not isinstance(css_class, str):
                config_errors.append(_('The css class must be a string.'))

        elif self.type == TypeItemFormulaire.TEXTE.name:
            text_size = self.config.get(CleConfigurationItemFormulaire.TAILLE_TEXTE.name)
            if text_size is not None and text_size not in self.valid_form_item_text_types:
                config_errors.append(
                    _('The text size must be one of the following values: %(values)s.')
                    % {'values': str(self.valid_form_item_text_types)}
                )

        elif self.type == TypeItemFormulaire.DOCUMENT.name:
            max_documents = self.config.get(CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name)
            if max_documents is not None and (not isinstance(max_documents, int) or max_documents < 1):
                config_errors.append(_('The maximum number of documents must be a positive number.'))
            mimetypes = self.config.get(CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name)
            if mimetypes is not None and (not isinstance(mimetypes, list) or not mimetypes):
                config_errors.append(_('The mimetypes must be a list with at least one mimetype.'))

        if config_errors:
            raise ValidationError(
                {
                    'config': config_errors,
                }
            )


class ConfigurableModelFormItemField(models.JSONField):
    """This model field can be used to store the data related to the AdmissionFormItem linked to an education."""

    def __init__(self, education_field_name='', upload_to='', *args, **kwargs):
        self.education_field_name = education_field_name
        self.upload_to = upload_to

        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        # Convert all writing tokens to UUIDs by remotely confirming their upload, leaving existing uuids
        current_value = super().pre_save(model_instance, add)

        field_configurations = AdmissionFormItem.objects.filter(
            education_id=getattr(model_instance, self.education_field_name),
            type=TypeItemFormulaire.DOCUMENT.name,
        ).exclude(deleted=True)

        for field_config in field_configurations:
            data_key = str(field_config.uuid)
            if current_value.get(data_key):
                current_value[data_key] = [
                    self._confirm_upload(model_instance, token) if ':' in token else token
                    for token in current_value[data_key]
                ]

        setattr(model_instance, self.attname, current_value)

        return current_value

    def _confirm_upload(self, model_instance, token):
        from osis_document.api.utils import confirm_remote_upload, get_remote_metadata

        # Get the current filename by interrogating API
        filename = get_remote_metadata(token)['name']

        return str(
            confirm_remote_upload(
                token=token,
                upload_to=dirname(generate_filename(model_instance, filename, self.upload_to)),
            )
        )
