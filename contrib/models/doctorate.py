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
from typing import Optional

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.models.person import Person
from osis_signature.contrib.fields import SignatureProcessField
from .base import BaseAdmission
from .enums.actor_type import ActorType


class DoctorateAdmission(BaseAdmission):
    doctoral_commission = models.ForeignKey(
        to="base.Entity",
        verbose_name=_("Doctoral commission"),
        related_name="+",
        on_delete=models.CASCADE,
        null=True,
    )

    committee = SignatureProcessField()

    class Meta:
        verbose_name = _("Doctorate admission")
        ordering = ('-created',)
        permissions = [
            ('access_doctorateadmission', _("Can access doctorate admissions")),
            ('download_jury_approved_pdf', _("Can download jury-approved PDF")),
            ('upload_jury_approved_pdf', _("Can upload jury-approved PDF")),
            ('upload_signed_scholarship', _("Can upload signed scholarship")),
            ('check_publication_authorisation', _("Can check publication autorisation")),
            ('validate_registration', _("Can validate registration")),
            ('approve_jury', _("Can approve jury")),
            ('approve_confirmation_paper', _("Can approve confirmation paper")),
            ('validate_doctoral_training', _("Can validate doctoral training")),
            ('download_pdf_confirmation', _("Can download PDF confirmation")),
            ('upload_pdf_confirmation', _("Can upload PDF confirmation")),
            ('fill_thesis', _("Can fill thesis")),
            ('submit_thesis', _("Can submit thesis")),
            ('appose_cdd_notice', _("Can appose CDD notice")),
            ('appose_sic_notice', _("Can appose SIC notice")),
            ('upload_defense_report', _("Can upload defense report")),
            ('check_copyright', _("Can check copyright")),
            ('sign_diploma', _("Can sign diploma")),
        ]

    def get_absolute_url(self):
        return reverse("admissions:doctorate-detail", args=[self.pk])

    @property
    def main_promoter(self) -> Optional[Person]:
        if not self.committee_id:
            return None
        actor = self.committee.actors.filter(committeeactor__type=ActorType.MAIN_PROMOTER.name).first()
        if actor:
            return actor.person
