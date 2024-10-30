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

import uuid

from ckeditor.fields import RichTextField
from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel

from osis_profile.models import EducationalExperience


class RefusalReasonCategory(OrderedModel):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
    )

    def __str__(self):
        return self.name

    class Meta(OrderedModel.Meta):
        verbose_name = _('Refusal reason category')
        verbose_name_plural = _('Refusal reason categories')


class RefusalReason(OrderedModel):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )

    name = RichTextField(
        verbose_name=_('Name'),
        config_name='link_only',
    )

    category = models.ForeignKey(
        on_delete=models.CASCADE,
        to=RefusalReasonCategory,
        verbose_name=_('Category'),
    )

    order_with_respect_to = 'category'

    def __str__(self):
        return mark_safe(self.name)

    class Meta(OrderedModel.Meta):
        verbose_name = _('Refusal reason')
        verbose_name_plural = _('Refusal reasons')


class AdditionalApprovalCondition(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )

    name_fr = RichTextField(
        verbose_name=_('French name'),
        config_name='link_only',
    )

    name_en = RichTextField(
        verbose_name=_('English name'),
        config_name='link_only',
    )

    order = models.FloatField(
        default=0,
        verbose_name=_('Order'),
    )

    def __str__(self):
        return {
            settings.LANGUAGE_CODE_FR: self.name_fr,
            settings.LANGUAGE_CODE_EN: self.name_en,
        }[settings.LANGUAGE_CODE]

    class Meta:
        verbose_name = _('Additional approval condition')
        verbose_name_plural = _('Additional approval conditions')
        ordering = ['order']


FREE_ADDITIONAL_APPROVAL_CONDITION_FIELD_BY_LANGUAGE = {
    settings.LANGUAGE_CODE_FR: 'name_fr',
    settings.LANGUAGE_CODE_EN: 'name_en',
}


class BaseFreeAdditionalApprovalCondition(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )

    name_fr = models.TextField(
        verbose_name=_('French name'),
        blank=True,
        default='',
    )

    name_en = models.TextField(
        verbose_name=_('English name'),
        blank=True,
        default='',
    )

    related_experience = models.ForeignKey(
        on_delete=models.PROTECT,
        to=EducationalExperience,
        verbose_name=_('Related experience'),
        blank=True,
        null=True,
        to_field='uuid',
    )

    def __str__(self):
        return {
            settings.LANGUAGE_CODE_FR: self.name_fr,
            settings.LANGUAGE_CODE_EN: self.name_en,
        }[settings.LANGUAGE_CODE]

    class Meta:
        abstract = True


class FreeAdditionalApprovalCondition(BaseFreeAdditionalApprovalCondition):
    admission = models.ForeignKey(
        on_delete=models.CASCADE,
        to='GeneralEducationAdmission',
        verbose_name=_('Admission'),
    )

    class Meta:
        verbose_name = _('Free additional approval condition')
        verbose_name_plural = _('Free additional approval conditions')
