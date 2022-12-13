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
import string
import uuid

import factory
from factory.fuzzy import FuzzyText

from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.ddd.admission.enums import ChoixTypeCompteBancaire
from admission.ddd.admission.formation_continue.domain.model._comptabilite import Comptabilite
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity, Proposition


class _ComptabiliteFactory(factory.Factory):
    class Meta:
        model = Comptabilite
        abstract = False

    # Affiliations
    etudiant_solidaire = False
    type_numero_compte = ChoixTypeCompteBancaire.NON

    # Compte bancaire
    numero_compte_iban = 'BE43068999999501'
    iban_valide = True
    numero_compte_autre_format = '123456'
    code_bic_swift_banque = 'GKCCBEBB'
    prenom_titulaire_compte = 'John'
    nom_titulaire_compte = 'Doe'


class _PropositionIdentityFactory(factory.Factory):
    class Meta:
        model = PropositionIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class PropositionFactory(factory.Factory):
    class Meta:
        model = Proposition
        abstract = False

    entity_id = factory.SubFactory(_PropositionIdentityFactory)
    matricule_candidat = FuzzyText(length=10, chars=string.digits)
    formation_id = factory.SubFactory(FormationIdentityFactory)
    creee_le = factory.Faker('past_datetime')
    modifiee_le = factory.Faker('past_datetime')
    comptabilite = factory.SubFactory(_ComptabiliteFactory)
