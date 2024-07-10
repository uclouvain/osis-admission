# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models.utils.utils import ChoiceEnum


class EPCInjectionStatus(ChoiceEnum):
    OK = "OK"
    ERROR = "ERROR"
    PENDING = "PENDING"


class EPCInjection(models.Model):
    admission = models.ForeignKey(
        'admission.BaseAdmission',
        on_delete=models.CASCADE,
        related_name='epc_injection',
    )
    status = models.CharField(choices=EPCInjectionStatus.choices(), null=False, blank=True, default='', max_length=7)
    payload = models.JSONField(default=dict, blank=True)
    epc_responses = models.JSONField(default=list, blank=True)
