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

import factory

# FIXME import this factory from shared kernel when available
from ddd.logic.learning_unit.tests.factory.ucl_entity import UclEntityIdentityFactory
from admission.ddd.preparation.projet_doctoral.domain.model.doctorat import (
    DoctoratIdentity,
    Doctorat,
)


class _DoctoratIdentityFactory(factory.Factory):
    class Meta:
        model = DoctoratIdentity
        abstract = False

    sigle = factory.Sequence(lambda n: 'SIGLE%02d' % n)
    annee = factory.fuzzy.FuzzyInteger(1999, 2099)


class _DoctoratFactory(factory.Factory):
    class Meta:
        model = Doctorat
        abstract = False

    entity_id = factory.SubFactory(_DoctoratIdentityFactory)
    entite_ucl_id = factory.SubFactory(UclEntityIdentityFactory)


class DoctoratCDEFactory(_DoctoratFactory):
    entite_ucl_id = factory.SubFactory(UclEntityIdentityFactory, code='CDE')


class DoctoratCDSCFactory(_DoctoratFactory):
    entite_ucl_id = factory.SubFactory(UclEntityIdentityFactory, code='CDSC')
