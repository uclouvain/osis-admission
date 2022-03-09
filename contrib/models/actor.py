# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import models
from django.utils.translation import gettext_lazy as _

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.enums.actor_type import ActorType
from osis_document.contrib import FileField
from osis_signature.models import Actor


def actor_upload_directory_path(instance: 'SupervisionActor', filename):
    """Return the file upload directory path."""
    admission = DoctorateAdmission.objects.select_related('candidate').get(
        supervision_group=instance.process,
    )
    return 'admission/{}/{}/approvals/{}'.format(
        admission.candidate.uuid,
        admission.uuid,
        filename,
    )


class SupervisionActor(Actor):
    """This model extend Actor from OSIS-Signature"""

    type = models.CharField(
        default=ActorType.choices(),
        max_length=50,
    )
    internal_comment = models.TextField(
        default='',
        verbose_name=_('Internal comment'),
        blank=True,
    )
    rejection_reason = models.CharField(
        default='',
        max_length=50,
        blank=True,
        verbose_name=_('Rejection reason'),
    )
    pdf_from_candidate = FileField(
        min_files=1,
        max_files=1,
        mimetypes=['application/pdf'],
        verbose_name=_("PDF file"),
        upload_to=actor_upload_directory_path,
    )


class ExternalActorMixin(models.Model):
    """This mixin is used in Promoter and CAMember roles"""

    is_external = models.BooleanField(
        default=False,
    )
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=255,
        blank=True,
        default='',
    )
    institute = models.CharField(
        verbose_name=_("Institution"),
        max_length=255,
        blank=True,
        default='',
    )
    city = models.CharField(
        verbose_name=_("City"),
        max_length=255,
        blank=True,
        default='',
    )
    country = models.ForeignKey(
        'reference.Country',
        verbose_name=_("Country"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True
