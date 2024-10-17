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
import attr
import datetime
import factory

from decimal import Decimal
from typing import Optional


from admission.models.online_payment import PaymentMethod, PaymentStatus
from admission.ddd import MONTANT_FRAIS_DOSSIER


@attr.dataclass
class Paiement:
    uuid_proposition: str
    identifiant_paiement: str
    statut: str
    methode: str
    montant: Decimal
    url_checkout: str
    date_creation: datetime.datetime
    date_mise_a_jour: datetime.datetime
    date_expiration: Optional[datetime.datetime]


class PaiementFactory(factory.Factory):
    identifiant_paiement = factory.Sequence(lambda x: f'p_id_{x}')
    methode = factory.Iterator(PaymentMethod.get_names())
    statut = factory.Iterator(PaymentStatus.get_names())
    date_expiration = factory.Faker('future_datetime')
    date_mise_a_jour = factory.Faker('future_datetime')
    date_creation = factory.Faker('future_datetime')
    url_checkout = factory.Faker('url')
    montant = MONTANT_FRAIS_DOSSIER

    class Meta:
        model = Paiement
