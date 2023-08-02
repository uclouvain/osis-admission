# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.contrib.models.base import BaseAdmission
from base.models.utils.utils import ChoiceEnum


class PaymentStatus(ChoiceEnum):
    OPEN = 'open'
    CANCELED = 'canceled'
    PENDING = 'pending'
    EXPIRED = 'expired'
    FAILED = 'failed'
    PAID = 'paid'

    @property
    def open_payments(self):
        return [
            self.OPEN.name,
            self.PENDING.name
        ]


class PaymentMethod(ChoiceEnum):
    BANCONTACT = 'bancontact'
    CREDIT_CARD = 'creditcard'
    BANK_TRANSFER = 'banktransfer'


class OnlinePayment(models.Model):
    admission = models.ForeignKey(
        BaseAdmission,
        on_delete=models.CASCADE,
        related_name='online_payments',
    )

    payment_id = models.CharField(max_length=14)
    status = models.CharField(choices=PaymentStatus.choices(), max_length=10)
    expiration_date = models.DateTimeField(null=True)
    method = models.CharField(choices=PaymentMethod.choices(), max_length=17, blank=True)
    creation_date = models.DateTimeField()
    updated_date = models.DateTimeField()
    dashboard_url = models.URLField()
    checkout_url = models.URLField(blank=True)
    payment_url = models.URLField()
    amount = models.DecimalField(decimal_places=2, max_digits=6)
