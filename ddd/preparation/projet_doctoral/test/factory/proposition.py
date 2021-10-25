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
import string
import uuid

import factory

from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import DetailProjet
from admission.ddd.preparation.projet_doctoral.domain.model._experience_precedente_recherche import \
    aucune_experience_precedente_recherche
from admission.ddd.preparation.projet_doctoral.domain.model._financement import financement_non_rempli
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import (
    PropositionIdentity,
    Proposition,
)
from admission.ddd.preparation.projet_doctoral.domain.model._enums import (
    ChoixStatusProposition,
    ChoixTypeAdmission,
)
from admission.ddd.preparation.projet_doctoral.test.factory.doctorat import _DoctoratIdentityFactory


class _PropositionIdentityFactory(factory.Factory):
    class Meta:
        model = PropositionIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _DetailProjetFactory(factory.Factory):
    class Meta:
        model = DetailProjet
        abstract = False

    titre = 'Mon projet'
    resume = factory.Faker('sentence')
    documents = factory.LazyFunction(list)


class _PropositionFactory(factory.Factory):
    class Meta:
        model = Proposition
        abstract = False

    entity_id = factory.SubFactory(_PropositionIdentityFactory)
    matricule_candidat = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    doctorat_id = factory.SubFactory(_DoctoratIdentityFactory)
    status = ChoixStatusProposition.IN_PROGRESS
    projet = factory.SubFactory(_DetailProjetFactory)
    creee_le = factory.Faker('past_datetime')
    financement = financement_non_rempli
    experience_precedente_recherche = aucune_experience_precedente_recherche


class PropositionAdmissionSC3DPMinimaleFactory(_PropositionFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP')
    type_admission = ChoixTypeAdmission.ADMISSION
    doctorat_id = factory.SubFactory(_DoctoratIdentityFactory, sigle='SC3DP', annee=2020)


class PropositionAdmissionECGE3DPMinimaleFactory(_PropositionFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-ECGE3DP')
    type_admission = ChoixTypeAdmission.ADMISSION
    doctorat_id = factory.SubFactory(_DoctoratIdentityFactory, sigle='ECGE3DP', annee=2020)


class PropositionAdmissionSC3DPMinimaleAnnuleeFactory(PropositionAdmissionSC3DPMinimaleFactory):
    status = ChoixStatusProposition.CANCELLED


class PropositionPreAdmissionSC3DPMinimaleFactory(_PropositionFactory):
    type_admission = ChoixTypeAdmission.PRE_ADMISSION
    doctorat_id = factory.SubFactory(_DoctoratIdentityFactory, sigle='SC3DP', annee=2020)


class PropositionAdmissionSC3DPAvecMembresFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-membre')


class PropositionAdmissionSC3DPAvecMembresInvitesFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-membres-invites')
