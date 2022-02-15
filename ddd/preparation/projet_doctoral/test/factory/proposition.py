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

from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import (
    ChoixLangueRedactionThese,
    DetailProjet,
    projet_non_rempli,
)
from admission.ddd.preparation.projet_doctoral.domain.model._enums import (
    ChoixStatutProposition,
    ChoixTypeAdmission,
)
from admission.ddd.preparation.projet_doctoral.domain.model._experience_precedente_recherche import (
    aucune_experience_precedente_recherche,
)
from admission.ddd.preparation.projet_doctoral.domain.model._financement import (
    ChoixTypeFinancement,
    Financement,
    financement_non_rempli,
)
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.preparation.projet_doctoral.test.factory.doctorat import _DoctoratIdentityFactory


class _PropositionIdentityFactory(factory.Factory):
    class Meta:
        model = PropositionIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _FinancementFactory(factory.Factory):
    class Meta:
        model = Financement
        abstract = False

    type = ChoixTypeFinancement.SELF_FUNDING


class _DetailProjetFactory(factory.Factory):
    class Meta:
        model = DetailProjet
        abstract = False

    titre = 'Mon projet'
    resume = factory.Faker('sentence')
    documents = factory.LazyFunction(lambda: [str(uuid.uuid4())])
    langue_redaction_these = ChoixLangueRedactionThese.FRENCH
    graphe_gantt = factory.LazyFunction(lambda: [str(uuid.uuid4())])
    proposition_programme_doctoral = factory.LazyFunction(lambda: [str(uuid.uuid4())])


class _PropositionFactory(factory.Factory):
    class Meta:
        model = Proposition
        abstract = False

    entity_id = factory.SubFactory(_PropositionIdentityFactory)
    reference = factory.Faker('pystr_format', string_format='2#-300###')
    matricule_candidat = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    doctorat_id = factory.SubFactory(_DoctoratIdentityFactory)
    statut = ChoixStatutProposition.IN_PROGRESS
    projet = factory.SubFactory(_DetailProjetFactory)
    creee_le = factory.Faker('past_datetime')
    financement = factory.SubFactory(_FinancementFactory)
    experience_precedente_recherche = aucune_experience_precedente_recherche


class PropositionAdmissionSC3DPMinimaleFactory(_PropositionFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP')
    type_admission = ChoixTypeAdmission.ADMISSION
    doctorat_id = factory.SubFactory(_DoctoratIdentityFactory, sigle='SC3DP', annee=2020)


class PropositionAdmissionECGE3DPMinimaleFactory(_PropositionFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-ECGE3DP')
    type_admission = ChoixTypeAdmission.ADMISSION
    doctorat_id = factory.SubFactory(_DoctoratIdentityFactory, sigle='ECGE3DP', annee=2020)
    matricule_candidat = '0123456789'


class PropositionAdmissionESP3DPMinimaleFactory(_PropositionFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-ESP3DP')
    type_admission = ChoixTypeAdmission.ADMISSION
    doctorat_id = factory.SubFactory(_DoctoratIdentityFactory, sigle='ESP3DP', annee=2020)
    matricule_candidat = '0123456789'


class PropositionAdmissionSC3DPMinimaleAnnuleeFactory(PropositionAdmissionSC3DPMinimaleFactory):
    statut = ChoixStatutProposition.CANCELLED
    matricule_candidat = '0123456789'


class PropositionAdmissionSC3DPMinimaleSansDetailProjetFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-no-project')
    projet = projet_non_rempli


class PropositionAdmissionSC3DPMinimaleSansFinancementFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-no-financement')
    financement = financement_non_rempli


class PropositionAdmissionSC3DPMinimaleSansCotutelleFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-cotutelle-indefinie')


class PropositionAdmissionSC3DPMinimaleCotutelleSansPromoteurExterneFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-cotutelle-sans-promoteur-externe')


class PropositionAdmissionSC3DPMinimaleCotutelleAvecPromoteurExterneFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-cotutelle-avec-promoteur-externe')


class PropositionPreAdmissionSC3DPMinimaleFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-pre-admission')
    type_admission = ChoixTypeAdmission.PRE_ADMISSION


class PropositionAdmissionSC3DPAvecMembresFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-membre')


class PropositionAdmissionSC3DPAvecMembresEtCotutelleFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-membre-cotutelle')
    matricule_candidat = 'candidat'


class PropositionAdmissionSC3DPAvecMembresInvitesFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-membres-invites')


class PropositionAdmissionSC3DPSansPromoteurFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-sans-promoteur')


class PropositionAdmissionSC3DPSansMembreCAFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-sans-membre_CA')
    matricule_candidat = '0123456789'


class PropositionAdmissionSC3DPAvecPromoteurDejaApprouveFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteur-deja-approuve')


class PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(PropositionAdmissionSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-promoteurs-membres-deja-approuves')
    matricule_candidat = '0123456789'
