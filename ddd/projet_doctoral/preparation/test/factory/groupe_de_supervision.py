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
import uuid
from typing import List, Optional

import factory

from admission.ddd.projet_doctoral.preparation.domain.model._cotutelle import Cotutelle, pas_de_cotutelle
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutSignatureGroupeDeSupervision
from admission.ddd.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.projet_doctoral.preparation.domain.model._signature_promoteur import (
    ChoixEtatSignature,
    SignaturePromoteur,
)
from admission.ddd.projet_doctoral.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
)
from admission.ddd.projet_doctoral.preparation.test.factory.proposition import (
    _PropositionIdentityFactory,
)


class _PromoteurIdentityFactory(factory.Factory):
    class Meta:
        model = PromoteurIdentity
        abstract = False

    matricule = factory.Sequence(lambda n: 'MATRICULE%02d' % n)


class _MembreCAIdentityFactory(factory.Factory):
    class Meta:
        model = MembreCAIdentity
        abstract = False

    matricule = factory.Sequence(lambda n: 'MATRICULE%02d' % n)


class _SignaturePromoteurFactory(factory.Factory):
    class Meta:
        model = SignaturePromoteur
        abstract = False

    promoteur_id = factory.SubFactory(_PromoteurIdentityFactory)


class _SignatureMembreCAFactory(factory.Factory):
    class Meta:
        model = SignatureMembreCA
        abstract = False

    membre_CA_id = factory.SubFactory(_MembreCAIdentityFactory)


class _GroupeDeSupervisionIdentityFactory(factory.Factory):
    class Meta:
        model = GroupeDeSupervisionIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _GroupeDeSupervisionFactory(factory.Factory):
    class Meta:
        model = GroupeDeSupervision
        abstract = False

    entity_id = factory.SubFactory(_GroupeDeSupervisionIdentityFactory)
    proposition_id = factory.SubFactory(_PropositionIdentityFactory)
    signatures_promoteurs = factory.LazyFunction(list)
    signatures_membres_CA = factory.LazyFunction(list)
    cotutelle: Optional[Cotutelle] = pas_de_cotutelle


class _CotutelleFactory(factory.Factory):
    demande_ouverture = factory.LazyFunction(lambda: [str(uuid.uuid4())])

    class Meta:
        model = Cotutelle
        abstract = False


class GroupeDeSupervisionSC3DPFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP')
    cotutelle = factory.SubFactory(
        _CotutelleFactory,
        motivation="Runs in family",
        institution_fwb=False,
        institution="MIT",
    )


class GroupeDeSupervisionSC3DPCotutelleIndefinieFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-cotutelle-indefinie')
    cotutelle = None


class GroupeDeSupervisionSC3DPPreAdmissionFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-pre-admission')


class GroupeDeSupervisionSC3DPAvecPromoteurEtMembreFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-membre')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP')]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [_SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED)]
    )


class GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtCotutelleFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-membre-cotutelle')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP-externe'),
            _SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP'),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
        ]
    )
    cotutelle = factory.SubFactory(
        _CotutelleFactory,
        motivation="Runs in family",
        institution_fwb=False,
        institution="MIT",
    )


class GroupeDeSupervisionSC3DPCotutelleSansPromoteurExterneFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-cotutelle-sans-promoteur-externe')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP')]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [_SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED)]
    )
    cotutelle = factory.SubFactory(
        _CotutelleFactory,
        motivation="Runs in family",
        institution_fwb=False,
        institution="MIT",
    )


class GroupeDeSupervisionSC3DPCotutelleAvecPromoteurExterneFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-cotutelle-avec-promoteur-externe')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP'),
            _SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP-externe'),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [_SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED)]
    )
    cotutelle = factory.SubFactory(
        _CotutelleFactory,
        motivation="Runs in family",
        institution_fwb=False,
        institution="MIT",
    )


class GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtProjetIncompletFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-no-project')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP')]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [_SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED)]
    )
    cotutelle = pas_de_cotutelle


class GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtFinancementIncompletFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-no-financement')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP')]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [_SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED)]
    )
    cotutelle = pas_de_cotutelle


class GroupeDeSupervisionSC3DPAvecMembresInvitesFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-membres-invites')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP', etat=ChoixEtatSignature.INVITED)]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(
                membre_CA_id__matricule='membre-ca-SC3DP-invite', etat=ChoixEtatSignature.INVITED
            ),
            _SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
        ]
    )


class GroupeDeSupervisionSC3DPSansPromoteurFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-sans-promoteur')
    signatures_promoteurs: List[SignaturePromoteur] = []
    signatures_membres_CA = factory.LazyFunction(
        lambda: [_SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP')]
    )


class GroupeDeSupervisionSC3DPSansMembresCAFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-sans-membre_CA')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(
                promoteur_id__matricule='promoteur-SC3DP-unique', etat=ChoixEtatSignature.INVITED
            )
        ]
    )
    signatures_membres_CA: List[SignatureMembreCA] = []


class GroupeDeSupervisionSC3DPAvecPromoteurDejaApprouveEtAutrePromoteurFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-deja-approuve')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP', etat=ChoixEtatSignature.INVITED),
            _SignaturePromoteurFactory(
                promoteur_id__matricule='promoteur-SC3DP-deja-approuve',
                etat=ChoixEtatSignature.APPROVED,
            ),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [_SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED)]
    )
    cotutelle = pas_de_cotutelle


class GroupeDeSupervisionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(
        _PropositionIdentityFactory,
        uuid='uuid-SC3DP-promoteurs-membres-deja-approuves',
    )
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(
                promoteur_id__matricule='promoteur-SC3DP-deja-approuve',
                etat=ChoixEtatSignature.APPROVED,
            ),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.APPROVED),
            _SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.APPROVED),
        ]
    )
    cotutelle = pas_de_cotutelle
    statut_signature = ChoixStatutSignatureGroupeDeSupervision.SIGNING_IN_PROGRESS


class GroupeDeSupervisionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory(_GroupeDeSupervisionFactory):
    proposition_id = factory.SubFactory(
        _PropositionIdentityFactory,
        uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve',
    )
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(
                promoteur_id__matricule='promoteur-SC3DP',
                etat=ChoixEtatSignature.DECLINED,
            ),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.APPROVED),
        ]
    )
    cotutelle = pas_de_cotutelle


class GroupeDeSupervisionPreSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(
    GroupeDeSupervisionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
):
    proposition_id = factory.SubFactory(
        _PropositionIdentityFactory,
        uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves',
    )
