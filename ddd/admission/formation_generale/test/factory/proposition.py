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

from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.test.factory.bourse import BourseIdentityFactory
from admission.ddd.admission.test.factory.formation import _FormationIdentityFactory


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
    formation_id = factory.SubFactory(_FormationIdentityFactory)

    creee_le = factory.Faker('past_datetime')
    modifiee_le = factory.Faker('past_datetime')

    bourse_double_diplome_id = factory.SubFactory(BourseIdentityFactory, uuid='a0e94dd5-3715-49a1-8953-8cc0f99372cb')
    bourse_internationale_id = factory.SubFactory(BourseIdentityFactory, uuid='c0e94dd5-3715-49a1-8953-8cc0f99372cb')
    bourse_erasmus_mundus_id = factory.SubFactory(BourseIdentityFactory, uuid='e0e94dd5-3715-49a1-8953-8cc0f99372cb')
    est_reorientation_inscription_externe = False
    est_modification_inscription_externe = False
