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
import uuid

import factory

from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmationIdentity,
    EpreuveConfirmation,
)
from admission.ddd.projet_doctoral.validation.test.factory.demande import _DemandeIdentityFactory


class _EpreuveConfirmationIdentityFactory(factory.Factory):
    class Meta:
        model = EpreuveConfirmationIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _EpreuveConfirmationFactory(factory.Factory):
    class Meta:
        model = EpreuveConfirmation
        abstract = False

    entity_id = factory.SubFactory(_EpreuveConfirmationIdentityFactory)
    date_limite = factory.Faker('future_date')


class EpreuveConfirmationDemandePreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(
    _EpreuveConfirmationFactory
):
    entity_id = factory.SubFactory(
        _EpreuveConfirmationIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves-1'
    )
    doctorat_id = factory.SubFactory(_DemandeIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves')
