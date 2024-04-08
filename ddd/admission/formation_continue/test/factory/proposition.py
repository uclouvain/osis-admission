# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixInscriptionATitre,
    ChoixStatutChecklist,
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity, Proposition
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import (
    StatutChecklist,
    StatutsChecklistContinue,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.ddd.admission.test.factory.reference import REFERENCE_MEMORY_ITERATOR


class _PropositionIdentityFactory(factory.Factory):
    class Meta:
        model = PropositionIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class StatutChecklistFactory(factory.Factory):
    class Meta:
        model = StatutChecklist
        abstract = False

    libelle = FuzzyText(length=10, chars=string.digits)
    enfants = factory.List([])
    statut = ChoixStatutChecklist.INITIAL_CANDIDAT
    extra = factory.Dict({})


class StatutsChecklistContinueFactory(factory.Factory):
    class Meta:
        model = StatutsChecklistContinue
        abstract = False

    fiche_etudiant = factory.SubFactory(StatutChecklistFactory)
    decision = factory.SubFactory(StatutChecklistFactory)


class PropositionFactory(factory.Factory):
    class Meta:
        model = Proposition
        abstract = False

    reference = factory.Iterator(REFERENCE_MEMORY_ITERATOR)
    entity_id = factory.SubFactory(_PropositionIdentityFactory)
    matricule_candidat = FuzzyText(length=10, chars=string.digits)
    formation_id = factory.SubFactory(FormationIdentityFactory)
    creee_le = factory.Faker('past_datetime')
    modifiee_le = factory.Faker('past_datetime')
    inscription_a_titre = ChoixInscriptionATitre.PRIVE

    class Params:
        est_confirmee = factory.Trait(
            statut=ChoixStatutPropositionContinue.CONFIRMEE,
            checklist_initiale=factory.SubFactory(StatutsChecklistContinueFactory),
            checklist_actuelle=factory.SubFactory(StatutsChecklistContinueFactory),
        )
        est_acceptee = factory.Trait(
            statut=ChoixStatutPropositionContinue.CONFIRMEE,
            checklist_initiale=factory.SubFactory(StatutsChecklistContinueFactory),
            checklist_actuelle=factory.SubFactory(
                StatutsChecklistContinueFactory,
                decision__statut=ChoixStatutChecklist.GEST_EN_COURS,
                decision__extra={'en_cours': 'fac_approval'},
            ),
        )
