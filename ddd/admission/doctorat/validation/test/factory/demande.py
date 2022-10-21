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

from admission.ddd.admission.doctorat.preparation.test.factory.proposition import _PropositionIdentityFactory
from admission.ddd.admission.doctorat.validation.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.doctorat.validation.domain.model.demande import Demande, DemandeIdentity
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC


class _DemandeIdentityFactory(factory.Factory):
    class Meta:
        model = DemandeIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class ProfilCandidatFactory(factory.Factory):
    class Meta:
        model = ProfilCandidat
        abstract = False


class _DemandeFactory(factory.Factory):
    class Meta:
        model = Demande
        abstract = False

    entity_id = factory.SubFactory(_DemandeIdentityFactory)
    statut_sic = ChoixStatutSIC.TO_BE_VERIFIED
    statut_cdd = ChoixStatutCDD.TO_BE_VERIFIED
    profil_candidat = factory.SubFactory(ProfilCandidatFactory)
    admission_confirmee_le = factory.Faker('past_datetime')


class DemandeAdmissionSC3DPMinimaleFactory(_DemandeFactory):
    entity_id = factory.SubFactory(_DemandeIdentityFactory, uuid='uuid-SC3DP')
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP')


class DemandePreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(_DemandeFactory):
    entity_id = factory.SubFactory(_DemandeIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves')
    proposition_id = factory.SubFactory(
        _PropositionIdentityFactory,
        uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves',
    )
    statut_cdd = ChoixStatutCDD.ACCEPTED
    statut_sic = ChoixStatutSIC.VALID
    admission_acceptee_le = factory.Faker('past_datetime')
    pre_admission_confirmee_le = factory.Faker('past_datetime')


class DemandeAdmissionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(_DemandeFactory):
    proposition_id = factory.SubFactory(
        _PropositionIdentityFactory,
        uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve',
    )
    entity_id = factory.SubFactory(_DemandeIdentityFactory, uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve')
    statut_cdd = ChoixStatutCDD.REJECTED
    statut_sic = ChoixStatutSIC.VALID


class DemandeAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(_DemandeFactory):
    entity_id = factory.SubFactory(_DemandeIdentityFactory, uuid='uuid-SC3DP-promoteurs-membres-deja-approuves')
    proposition_id = factory.SubFactory(
        _PropositionIdentityFactory,
        uuid='uuid-SC3DP-promoteurs-membres-deja-approuves',
    )
    statut_cdd = ChoixStatutCDD.ACCEPTED
    statut_sic = ChoixStatutSIC.VALID
    admission_acceptee_le = factory.Faker('past_datetime')
