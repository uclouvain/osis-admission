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
import re
from collections import OrderedDict
from inspect import getfullargspec

from django import forms
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.doctoral_training import Activity
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import CategorieActivite, StatutActivite
from admission.forms.doctorate.training import activity as activity_forms
from admission.forms.doctorate.training.activity import ConfigurableActivityTypeField
from osis_document.contrib import FileUploadField
from reference.api.serializers.country import RelatedCountryField

FORM_SERIALIZER_FIELD_MAPPING = {
    forms.CharField: serializers.CharField,
    forms.MultipleChoiceField: serializers.ChoiceField,
    forms.ChoiceField: serializers.ChoiceField,
    forms.BooleanField: serializers.BooleanField,
    forms.IntegerField: serializers.IntegerField,
    forms.EmailField: serializers.EmailField,
    forms.DateTimeField: serializers.DateTimeField,
    forms.DateField: serializers.DateField,
    forms.TimeField: serializers.TimeField,
    ConfigurableActivityTypeField: serializers.CharField,
    forms.URLField: serializers.CharField,
    forms.FloatField: serializers.FloatField,
    forms.TypedChoiceField: serializers.ChoiceField,  # "is_online" field
    forms.ModelChoiceField: serializers.Field,  # replaced correctly later
    FileUploadField: serializers.ListField,
}


def find_class_args(klass):
    """Find all class arguments (parameters) which can be passed in ``__init__``."""
    args = set()

    for i in klass.mro():
        if i is object or not hasattr(i, '__init__'):
            continue
        function_args = [i for i in getfullargspec(i.__init__)[0] if i not in ['self', 'cls']]
        args |= set(function_args)

    return list(args)


def find_matching_class_kwargs(reference_object, klass):
    return {arg: getattr(reference_object, arg) for arg in find_class_args(klass) if hasattr(reference_object, arg)}


class ActivitySerializerBase(serializers.Serializer):
    """Mixin for all activity serializers

    Aiming to
      - convert from fields to serializer
      - specify some fields' properties (e.g.: country and file uploads)
      - pass-through validation operations to the mapped Form.
    """

    child_classes = None

    def __init__(self, *args, child_classes=None, **kwargs):
        self.child_classes = child_classes
        self.form_instance = None
        super().__init__(*args, **kwargs)

    def get_form(self, data=None, **kwargs):
        """Create an instance of configured form class."""
        return self.Meta.form(data=data, **kwargs)

    def get_fields(self):
        """
        Return all the fields that should be serialized for the form.
        :return: dict of {'field_name': serializer_field_instance}
        """
        ret = super().get_fields()

        field_mapping = FORM_SERIALIZER_FIELD_MAPPING

        # Iterate over the form fields, creating an instance of serializer field for each.
        form = self.Meta.form
        for field_name, form_field in getattr(form, 'all_base_fields', form.base_fields).items():
            # Field is specified as excluded field
            if field_name in getattr(self.Meta, 'exclude', []):
                continue

            # Field is already defined via declared fields
            if field_name in ret:
                continue

            try:
                serializer_field_class = field_mapping[form_field.__class__]
            except KeyError:
                raise TypeError(
                    "{field} is not mapped to a serializer field. Please add {field} to FORM_SERIALIZER_FIELD_MAPPING."
                )
            else:
                ret[field_name] = self._get_field(field_name, form_field, serializer_field_class)

        # Add hint for serializer class
        ret['object_type'] = serializers.CharField()

        # Add useful fields (that are not in form)
        ret['uuid'] = serializers.CharField(read_only=True)
        ret['category'] = serializers.ChoiceField(choices=CategorieActivite.choices())
        ret['status'] = serializers.ChoiceField(choices=StatutActivite.choices(), read_only=True)
        ret['doctorate'] = serializers.PrimaryKeyRelatedField(
            queryset=DoctorateAdmission.objects.all(),
            write_only=True,
            required=False,
        )

        # Hierarchy handling
        mapping_key = [
            key
            for key, serializer in DoctoralTrainingActivitySerializer.serializer_class_mapping.items()
            if serializer == self.__class__
        ][0]
        if isinstance(mapping_key, tuple):
            ret['parent'] = serializers.SlugRelatedField(
                slug_field='uuid',
                queryset=Activity.objects.all(),
            )
        if self.child_classes:
            ret['children'] = serializers.ListSerializer(
                child=DoctoralTrainingActivitySerializer(only_classes=self.child_classes),
                read_only=True,
            )

        return ret

    def _get_field(self, field_name, form_field, serializer_field_class):
        kwargs = self._get_field_kwargs(form_field, serializer_field_class)

        if field_name == 'country':
            serializer_field_class = RelatedCountryField
            kwargs = {}

        field = serializer_field_class(**kwargs)

        for kwarg, value in kwargs.items():
            # set corresponding DRF attributes which don't have alternative
            # in Django form fields
            if kwarg == 'required':
                field.allow_blank = not value
                field.allow_null = not value

            # ChoiceField natively uses choice_strings_to_values
            # in the to_internal_value flow
            elif kwarg == 'choices':
                field.choice_strings_to_values = {str(key): key for key in OrderedDict(value).keys()}

        return field

    def _get_field_kwargs(self, form_field, serializer_field_class):
        """
        For a given Form field, determine what validation attributes
        have been set.  Includes things like max_length, required, etc.
        These will be used to create an instance of ``rest_framework.fields.Field``.
        :param form_field: a ``django.forms.field.Field`` instance
        :return: dictionary of attributes to set
        """
        attrs = find_matching_class_kwargs(form_field, serializer_field_class)

        if 'choices' in attrs:
            choices = OrderedDict(attrs['choices']).keys()
            attrs['choices'] = OrderedDict(zip(choices, choices))

        if getattr(form_field, 'initial', None):
            attrs['default'] = form_field.initial

        # avoid "May not set both `required` and `default`"
        if attrs.get('required') and 'default' in attrs:
            del attrs['required']

        if isinstance(form_field, FileUploadField):
            attrs['child'] = serializers.CharField()
        if isinstance(form_field, forms.CharField):
            attrs.setdefault('allow_blank', True)
        if isinstance(form_field, (forms.DateField, forms.TypedChoiceField)):
            attrs.setdefault('allow_null', True)
        attrs.pop('required', None)

        return attrs

    def validate(self, data):
        """
        Validate a form instance using the data that has been run through the serializer field validation.
        :param data: deserialized data to validate
        :return: validated, cleaned form data
        :raise: ``django.core.exceptions.ValidationError`` on failed validation.
        """
        self.form_instance = form = self.get_form(data=data)

        if not form.is_valid():
            raise serializers.ValidationError(form.errors)
        return form.cleaned_data


class ConferenceSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.ConferenceForm


class ConferenceCommunicationSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.ConferenceCommunicationForm


class ConferencePublicationSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.ConferencePublicationForm


class CommunicationSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.CommunicationForm


class PublicationSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.PublicationForm


class ResidencySerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.ResidencyForm


class ResidencyCommunicationSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.ResidencyCommunicationForm


class ServiceSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.ServiceForm


class SeminarSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.SeminarForm


class SeminarCommunicationSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.SeminarCommunicationForm


class ValorisationSerializer(ActivitySerializerBase):
    class Meta:
        form = activity_forms.ValorisationForm


class DoctoralTrainingActivitySerializer(serializers.Serializer):
    """Serializer that dispatches to activity serializers given the category and the presence of a parent."""

    serializer_class_mapping = {
        CategorieActivite.CONFERENCE: ConferenceSerializer,
        (CategorieActivite.CONFERENCE, CategorieActivite.COMMUNICATION): ConferenceCommunicationSerializer,
        (CategorieActivite.CONFERENCE, CategorieActivite.PUBLICATION): ConferencePublicationSerializer,
        CategorieActivite.RESIDENCY: ResidencySerializer,
        (CategorieActivite.RESIDENCY, CategorieActivite.COMMUNICATION): ResidencyCommunicationSerializer,
        CategorieActivite.COMMUNICATION: CommunicationSerializer,
        CategorieActivite.PUBLICATION: PublicationSerializer,
        CategorieActivite.SERVICE: ServiceSerializer,
        CategorieActivite.SEMINAR: SeminarSerializer,
        (CategorieActivite.SEMINAR, CategorieActivite.COMMUNICATION): SeminarCommunicationSerializer,
        CategorieActivite.VAE: ValorisationSerializer,
    }
    only_classes = None

    def __init__(self, *args, only_classes=None, **kwargs):
        self.only_classes = only_classes
        super().__init__(*args, **kwargs)

    def get_mapped_serializer_class(self, instance: Activity):
        if instance.parent_id:
            return self.serializer_class_mapping.get(
                (CategorieActivite[instance.parent.category], CategorieActivite[instance.category])
            )
        return self.serializer_class_mapping.get(CategorieActivite[instance.category])

    def to_representation(self, instance):
        serializer_class = self.get_mapped_serializer_class(instance)

        # Use the serializer's class name to hint which oneOf class to map to
        # by removing the "serializer" string from the class name.
        pattern = re.compile("serializer", re.IGNORECASE)
        instance.object_type = pattern.sub("", serializer_class.__name__)

        return serializer_class().to_representation(instance)

    def to_internal_value(self, data):
        mapping_key = CategorieActivite[data.get('category')]
        if data.get('parent'):
            parent = get_object_or_404(Activity.objects.filter(doctorate_id=data['doctorate']), uuid=data['parent'])
            mapping_key = (CategorieActivite[parent.category], CategorieActivite[data.get('category')])
        serializer_class = self.serializer_class_mapping.get(mapping_key)

        return serializer_class().to_internal_value(data)

    def create(self, validated_data):
        """Save a new activity object (simplified ModelSerializer mechanic)"""
        validated_data.pop('object_type')
        return Activity.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Save an existing activity object (simplified ModelSerializer mechanic)"""
        validated_data.pop('object_type')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
