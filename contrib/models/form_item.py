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
from collections import defaultdict
from os.path import dirname

import uuid as uuid
from typing import List

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _, ngettext_lazy, pgettext_lazy
from osis_document.utils import generate_filename, is_uuid

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.ddd import BE_ISO_CODE, FR_ISO_CODE, EN_ISO_CODE
from admission.ddd.admission.enums.question_specifique import (
    TypeItemFormulaire,
    CleConfigurationItemFormulaire,
    TypeChampTexteFormulaire,
    CritereItemFormulaireNationaliteCandidat,
    CritereItemFormulaireLangueEtudes,
    CritereItemFormulaireVIP,
    Onglets,
    CritereItemFormulaireFormation,
)
from admission.forms.translation_field import TranslatedValueField
from base.models.person import Person
from osis_profile.models import EducationalExperience

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


def is_completed_translated_json_field(value):
    if not value:
        return False
    return all(value.get(language) for language in TRANSLATION_LANGUAGES)


class TranslatedJSONField(models.JSONField):
    def __init__(self, **kwargs):
        kwargs.setdefault('default', dict)
        kwargs.setdefault('validators', [is_valid_translated_json_field])
        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        return super().formfield(
            form_class=TranslatedValueField,
            show_hidden_initial=False,
            **kwargs,
        )


class AdmissionFormItem(models.Model):
    """This model stores the configuration of a dynamic form field."""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    academic_years = models.ManyToManyField(
        'base.AcademicYear',
        through='AdmissionFormItemInstantiation',
        related_name='+',
    )
    internal_label = models.CharField(
        max_length=255,
        verbose_name=_('Internal label'),
    )
    type = models.CharField(
        choices=TypeItemFormulaire.choices(),
        max_length=30,
    )
    title = TranslatedJSONField(
        blank=True,
        verbose_name=_('Title'),
        help_text=_('Question label for Document and Text form elements. Not used for Message elements.'),
    )
    text = TranslatedJSONField(
        blank=True,
        verbose_name=_('Text'),
        help_text=_(
            'Question tooltip text for Document and Text form elements. Content of the message to be displayed for '
            'Message elements.'
        ),
    )
    help_text = TranslatedJSONField(
        blank=True,
        verbose_name=_('Help text'),
        help_text=_('Placeholder text for Text form elements. Not used for Document and Message elements.'),
    )
    active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Indicates if the item will be displayed to the user or not.'),
    )
    configuration = models.JSONField(
        blank=True,
        default=dict,
        verbose_name=_('Configuration'),
        help_text=_(
            'For a message, it is possible to specify the CSS class that we want to apply on it by using the '
            '"CLASSE_CSS" property. This is a string which can contain several classes, separated with a space. '
            '<a href="https://getbootstrap.com/docs/3.3/css/#helper-classes">Bootstrap classes</a> can be used '
            'here.<br>Full example: <code>{"CLASSE_CSS": "bg-info"}</code>.<br><br>'
            'For a text field, it is possible to specify if the user can enter a short ("COURT", by default) or a '
            'long ("LONG") text by using the "TAILLE_TEXTE" property.<br>'
            'Full example: <code>{"TAILLE_TEXTE": "LONG"}</code>.<br><br>'
            'For a file field, it is possible to specify the maximum number '
            '("NOMBRE_MAX_DOCUMENT", default to 1) and the MIME types ("TYPES_MIME_FICHIER") of the files '
            'that can be uploaded.<br>'
            'Full example: <code>{"TYPES_MIME_FICHIER": ["application/pdf"], "NOMBRE_MAX_DOCUMENTS": 3}</code>.'
        ),
    )

    def __str__(self):
        return f'{self.id} - {self.internal_label}'

    class Meta:
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
        errors = defaultdict(list)

        invalid_config_keys = [
            key for key in self.configuration if key not in self.config_allowed_properties[self.type]
        ]

        if invalid_config_keys:
            errors['configuration'].append(
                ngettext_lazy(
                    'Invalid property: %(config_params)s',
                    'Invalid properties: %(config_params)s',
                    len(invalid_config_keys),
                )
                % {'config_params': ','.join(invalid_config_keys)}
            )

        if self.type == TypeItemFormulaire.MESSAGE.name:
            css_class = self.configuration.get(CleConfigurationItemFormulaire.CLASSE_CSS.name)

            if css_class is not None and not isinstance(css_class, str):
                errors['configuration'].append(_('The css class must be a string.'))

            if not is_completed_translated_json_field(self.text):
                errors['text'].append(FIELD_REQUIRED_MESSAGE)

        elif self.type == TypeItemFormulaire.TEXTE.name:
            text_size = self.configuration.get(CleConfigurationItemFormulaire.TAILLE_TEXTE.name)

            if text_size is not None and text_size not in self.valid_form_item_text_types:
                errors['configuration'].append(
                    _('The text size must be one of the following values: %(values)s.')
                    % {'values': str(self.valid_form_item_text_types)}
                )

            if not is_completed_translated_json_field(self.title):
                errors['title'].append(FIELD_REQUIRED_MESSAGE)

        elif self.type == TypeItemFormulaire.DOCUMENT.name:
            max_documents = self.configuration.get(CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name)

            if max_documents is not None and (not isinstance(max_documents, int) or max_documents < 1):
                errors['configuration'].append(_('The maximum number of documents must be a positive number.'))

            mimetypes = self.configuration.get(CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name)

            if mimetypes is not None and (not isinstance(mimetypes, list) or not mimetypes):
                errors['configuration'].append(_('The mimetypes must be a list with at least one mimetype.'))

            if not is_completed_translated_json_field(self.title):
                errors['title'].append(FIELD_REQUIRED_MESSAGE)

        if errors:
            raise ValidationError(errors)


class AdmissionFormItemInstantiationManager(models.Manager):
    def get_nationality_criteria_by_candidate(self, candidate: Person):
        criteria = [CritereItemFormulaireNationaliteCandidat.TOUS.name]

        if candidate.country_of_citizenship_id:
            if candidate.country_of_citizenship.iso_code == BE_ISO_CODE:
                criteria.append(CritereItemFormulaireNationaliteCandidat.BELGE.name)
            else:
                criteria.append(CritereItemFormulaireNationaliteCandidat.NON_BELGE.name)

            if candidate.country_of_citizenship.european_union:
                criteria.append(CritereItemFormulaireNationaliteCandidat.UE.name)
            else:
                criteria.append(CritereItemFormulaireNationaliteCandidat.NON_UE.name)

        return criteria

    def get_study_language_criteria_by_candidate(self, candidate: Person):
        studied_in_french = False
        studied_in_english = False

        # Check secondary studies
        if hasattr(candidate, 'belgianhighschooldiploma'):
            studied_in_french = True
            studied_in_english = True
        elif hasattr(candidate, 'foreignhighschooldiploma') and getattr(
            candidate.foreignhighschooldiploma.linguistic_regime,
            'code',
            None,
        ):
            if candidate.foreignhighschooldiploma.linguistic_regime.code == FR_ISO_CODE:
                studied_in_french = True
            elif candidate.foreignhighschooldiploma.linguistic_regime.code == EN_ISO_CODE:
                studied_in_english = True

        # Check higher studies
        if not studied_in_french or not studied_in_english:
            educational_experiences_languages = set(
                EducationalExperience.objects.filter(person=candidate).values_list('linguistic_regime__code', flat=True)
            )

            if FR_ISO_CODE in educational_experiences_languages:
                studied_in_french = True

            if EN_ISO_CODE in educational_experiences_languages:
                studied_in_english = True

            if None in educational_experiences_languages:
                # Belgian experiences
                studied_in_english = True
                studied_in_french = True

        criteria = [CritereItemFormulaireLangueEtudes.TOUS.name]
        if not studied_in_french:
            criteria.append(CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_FR.name)
        if not studied_in_english:
            criteria.append(CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_EN.name)

        return criteria

    def get_vip_criteria(self, admission):
        criteria = [CritereItemFormulaireVIP.TOUS.name]
        if any(
            getattr(admission, scholarship, None)
            for scholarship in [
                'erasmus_mundus_scholarship_id',
                'double_degree_scholarship_id',
                'international_scholarship_id',
            ]
        ):
            criteria.append(CritereItemFormulaireVIP.VIP.name)
        else:
            criteria.append(CritereItemFormulaireVIP.NON_VIP.name)

        return criteria

    def form_items_by_admission(
        self,
        admission,
        tabs: List[str] = None,
        form_item_type: str = '',
        required: bool = None,
        candidate: Person = None,
    ):
        qs: models.QuerySet['AdmissionFormItemInstantiation'] = super().get_queryset()
        if not candidate:
            candidate = admission.candidate

        if tabs:
            qs = qs.filter(tab__in=tabs)

        if form_item_type:
            qs = qs.filter(form_item__type=form_item_type)

        if required is not None:
            qs = qs.filter(required=required)

        return (
            qs.filter(
                form_item__active=True,
                academic_year_id=admission.determined_academic_year_id or admission.training.academic_year_id,
                candidate_nationality__in=self.get_nationality_criteria_by_candidate(candidate),
                study_language__in=self.get_study_language_criteria_by_candidate(candidate),
                vip_candidate__in=self.get_vip_criteria(admission),
            )
            .filter(
                Q(display_according_education=CritereItemFormulaireFormation.TOUTE_FORMATION.name)
                | Q(education_group__pk=admission.training.education_group_id)
                | Q(education_group_type__pk=admission.training.education_group_type_id)
            )
            .select_related('form_item')
        )


class AdmissionFormItemInstantiation(models.Model):
    """
    This model stores the configuration of a dynamic form field for a specific year, education group or education
    group year.
    """

    form_item = models.ForeignKey(
        on_delete=models.PROTECT,
        to='AdmissionFormItem',
        verbose_name=_('Form item'),
    )
    academic_year = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='+',
        to='base.AcademicYear',
        verbose_name=_('Academic year'),
    )
    weight = models.PositiveIntegerField(
        verbose_name=_('Weight'),
        help_text=_(
            'An integer greater than zero indicating the position of the item in relation to the others. Important '
            'point: the questions are displayed together according to the field "Display according to training" (the '
            'elements for all trainings, then the elements for a type of training, then the elements for a specific '
            'training).'
        ),
    )
    required = models.BooleanField(
        default=False,
        verbose_name=_('Required'),
    )
    display_according_education = models.CharField(
        choices=CritereItemFormulaireFormation.choices(),
        max_length=30,
        verbose_name=_('Display according education'),
    )
    education_group_type = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        to='base.EducationGroupType',
        verbose_name=_('Type of training'),
    )
    education_group = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        to='base.EducationGroup',
        verbose_name=pgettext_lazy('admission', 'Education'),
    )
    candidate_nationality = models.CharField(
        choices=CritereItemFormulaireNationaliteCandidat.choices(),
        default=CritereItemFormulaireNationaliteCandidat.TOUS.name,
        max_length=30,
        verbose_name=_('Candidate nationality'),
    )
    study_language = models.CharField(
        choices=CritereItemFormulaireLangueEtudes.choices(),
        default=CritereItemFormulaireLangueEtudes.TOUS.name,
        max_length=30,
        verbose_name=_('Study language'),
        help_text=_(
            'Takes into account the language of secondary and higher education. Studies in Belgium are considered as '
            'both French and English studies.'
        ),
    )
    vip_candidate = models.CharField(
        choices=CritereItemFormulaireVIP.choices(),
        default=CritereItemFormulaireVIP.TOUS.name,
        max_length=30,
        verbose_name=_('VIP candidate'),
        help_text=_(
            'A candidate is considered as VIP if he/she is in double degree or if he/she benefits from an '
            'international scholarship or if he/she is Erasmus Mundus.'
        ),
    )
    tab = models.CharField(
        choices=Onglets.choices(),
        max_length=30,
        verbose_name=_('Tab'),
    )

    objects = AdmissionFormItemInstantiationManager()

    def __str__(self):
        return f'{self.form_item}-{self.academic_year}'

    class Meta:
        verbose_name = _('Admission form item instantiation')
        verbose_name_plural = _('Admission form item instantiations')

    def clean(self):
        errors = {}

        if self.display_according_education == CritereItemFormulaireFormation.UNE_FORMATION.name:
            self.education_group_type_id = None
            if not self.education_group_id:
                errors['education_group'] = FIELD_REQUIRED_MESSAGE

        elif self.display_according_education == CritereItemFormulaireFormation.TYPE_DE_FORMATION.name:
            self.education_group_id = None
            if not self.education_group_type_id:
                errors['education_group_type'] = FIELD_REQUIRED_MESSAGE

        elif self.display_according_education == CritereItemFormulaireFormation.TOUTE_FORMATION.name:
            self.education_group_type_id = None
            self.education_group_id = None

        if errors:
            raise ValidationError(errors)


class ConfigurableModelFormItemField(models.JSONField):
    """This model field can be used to store the data related to the AdmissionFormItem linked to an education."""

    def __init__(self, education_field_name='', upload_to='', *args, **kwargs):
        self.education_field_name = education_field_name
        self.upload_to = upload_to

        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        # Convert all writing file tokens to UUIDs by remotely confirming their upload, leaving existing uuids
        current_value = super().pre_save(model_instance, add) or {}

        document_field_configurations: models.QuerySet[AdmissionFormItem] = AdmissionFormItem.objects.filter(
            uuid__in=current_value.keys(),
            type=TypeItemFormulaire.DOCUMENT.name,
        )

        for field_config in document_field_configurations:
            data_key = str(field_config.uuid)
            current_value[data_key] = [
                self._confirm_upload(model_instance, token) if not is_uuid(token) else token
                for token in current_value[data_key]
            ]

        setattr(model_instance, self.attname, current_value)

        return current_value

    def _confirm_upload(self, model_instance, token):
        from osis_document.api.utils import confirm_remote_upload, get_remote_metadata

        # Get the current filename by interrogating API
        filename = get_remote_metadata(token).get('name', 'filename')

        return str(
            confirm_remote_upload(
                token=token,
                upload_to=dirname(generate_filename(model_instance, filename, self.upload_to)),
            )
        )
