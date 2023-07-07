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
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class RefusalReasonCategory(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )

    name_fr = models.CharField(
        max_length=255,
        verbose_name=_('French name'),
    )

    name_en = models.CharField(
        max_length=255,
        verbose_name=_('English name'),
    )

    def __str__(self):
        return {
            settings.LANGUAGE_CODE_FR: self.name_fr,
            settings.LANGUAGE_CODE_EN: self.name_en,
        }[settings.LANGUAGE_CODE]

    class Meta:
        verbose_name = _('Refusal reason category')
        verbose_name_plural = _('Refusal reason categories')


class RefusalReason(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )

    name_fr = models.CharField(
        max_length=255,
        verbose_name=_('French name'),
    )

    name_en = models.CharField(
        max_length=255,
        verbose_name=_('English name'),
    )

    category = models.ForeignKey(
        on_delete=models.CASCADE,
        to=RefusalReasonCategory,
        verbose_name=_('Category'),
    )

    def __str__(self):
        return {
            settings.LANGUAGE_CODE_FR: self.name_fr,
            settings.LANGUAGE_CODE_EN: self.name_en,
        }[settings.LANGUAGE_CODE]

    class Meta:
        verbose_name = _('Refusal reason')
        verbose_name_plural = _('Refusal reasons')


class AdditionalApprovalCondition(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )

    name_fr = models.CharField(
        max_length=255,
        verbose_name=_('French name'),
    )

    name_en = models.CharField(
        max_length=255,
        verbose_name=_('English name'),
    )

    def __str__(self):
        return {
            settings.LANGUAGE_CODE_FR: self.name_fr,
            settings.LANGUAGE_CODE_EN: self.name_en,
        }[settings.LANGUAGE_CODE]

    class Meta:
        verbose_name = _('Additional approval condition')
        verbose_name_plural = _('Additional approval conditions')
