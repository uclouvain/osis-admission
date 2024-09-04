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
import factory
from factory.django import DjangoModelFactory

from admission.contrib.models.online_payment import OnlinePayment, PaymentMethod, PaymentStatus
from admission.ddd import MONTANT_FRAIS_DOSSIER
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory


class OnlinePaymentFactory(DjangoModelFactory):
    admission = factory.SubFactory(GeneralEducationAdmissionFactory)
    payment_id = factory.Sequence(lambda x: f'p_id_{x}')
    method = factory.Iterator(PaymentMethod.get_names())
    status = factory.Iterator(PaymentStatus.get_names())
    expiration_date = factory.Faker('future_datetime')
    updated_date = factory.Faker('future_datetime')
    creation_date = factory.Faker('future_datetime')
    dashboard_url = factory.Faker('url')
    checkout_url = factory.Faker('url')
    payment_url = factory.Faker('url')
    amount = MONTANT_FRAIS_DOSSIER

    class Meta:
        model = OnlinePayment
