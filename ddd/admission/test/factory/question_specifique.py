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
import factory
import uuid

import attr

from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
)
from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifiqueIdentity, QuestionSpecifique
from admission.ddd.admission.enums.question_specifique import TypeItemFormulaire, Onglets
from admission.ddd.admission.formation_continue.test.factory.proposition import (
    PropositionFactory as PropositionContinueFactory,
)
from admission.ddd.admission.formation_generale.test.factory.proposition import (
    PropositionFactory as PropositionGeneraleFactory,
)


class QuestionSpecifiqueIdentityFactory(factory.Factory):
    class Meta:
        model = QuestionSpecifiqueIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


@attr.dataclass(frozen=True, slots=True)
class QuestionSpecifiqueFormationGenerale(QuestionSpecifique):
    proposition = factory.SubFactory(PropositionGeneraleFactory)
    active: bool = True


@attr.dataclass(frozen=True, slots=True)
class QuestionSpecifiqueFormationContinue(QuestionSpecifique):
    proposition = factory.SubFactory(PropositionContinueFactory)
    active: bool = True


@attr.dataclass(frozen=True, slots=True)
class QuestionSpecifiqueFormationDoctorale(QuestionSpecifique):
    proposition = factory.SubFactory(PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory)
    active: bool = True


@attr.dataclass(frozen=True, slots=True)
class QuestionSpecifiqueEtendue(QuestionSpecifique):
    active: bool = True


class QuestionSpecifiqueFactory(factory.Factory):
    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    type = factory.Iterator(TypeItemFormulaire.get_names())
    poids = factory.Faker('number')
    label_interne = factory.Faker('sentence')
    requis = False
    titre = attr.Factory(dict)
    texte = attr.Factory(dict)
    texte_aide = attr.Factory(dict)
    configuration = attr.Factory(dict)
    onglet = factory.Iterator(Onglets.get_names())

    class Meta:
        model = QuestionSpecifiqueEtendue
