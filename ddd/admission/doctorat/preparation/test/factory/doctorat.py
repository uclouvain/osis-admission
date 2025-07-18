# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

import attr
import factory.fuzzy

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    DoctoratFormation,
)

# FIXME import this factory from shared kernel when available
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratFormationDTO
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.repository.i_proposition import CAMPUS_LETTRE_DOSSIER
from admission.ddd.admission.test.factory.formation import (
    CampusFactory,
    FormationIdentityFactory,
)
from base.models.enums.education_group_types import TrainingType
from ddd.logic.learning_unit.tests.factory.ucl_entity import UclEntityIdentityFactory


class _DoctoratIdentityFactory(factory.Factory):
    class Meta:
        model = FormationIdentity
        abstract = False

    sigle = factory.Sequence(lambda n: 'SIGLE%02d' % n)
    annee = factory.fuzzy.FuzzyInteger(1999, 2099)


@attr.dataclass(frozen=True, slots=True)
class DoctoratFormationEtendu(DoctoratFormation):
    campus: str
    intitule: str
    sigle: str
    campus_inscription: str
    code_secteur: str
    intitule_secteur: str
    grade_academique: str


class _DoctoratFactory(factory.Factory):
    class Meta:
        model = DoctoratFormationEtendu
        abstract = False

    entity_id = factory.SubFactory(FormationIdentityFactory)
    entite_ucl_id = factory.SubFactory(UclEntityIdentityFactory)
    campus = factory.Iterator(CAMPUS_LETTRE_DOSSIER.keys())
    campus_inscription = factory.Iterator(CAMPUS_LETTRE_DOSSIER.keys())
    intitule = factory.Faker('sentence')
    intitule_fr = factory.Faker('sentence')
    intitule_en = factory.Faker('sentence')
    intitule_secteur = factory.Faker('sentence')
    sigle = factory.Faker('word')
    code_secteur = factory.Faker('word')
    type = TrainingType.PHD
    grade_academique = '1'


class _DoctoratDTOFactory(factory.Factory):
    class Meta:
        model = DoctoratFormationDTO
        abstract = False

    code = factory.Sequence(lambda n: 'CODE%02d' % n)
    intitule = factory.Faker('sentence')
    intitule_fr = factory.Faker('sentence')
    intitule_en = factory.Faker('sentence')
    campus = CampusFactory()
    campus_inscription = CampusFactory()
    date_debut = factory.Faker('date')
    type = TrainingType.PHD.name
    credits = 180
    grade_academique = '1'


class DoctoratCDEFactory(_DoctoratFactory):
    entite_ucl_id = factory.SubFactory(UclEntityIdentityFactory, code='CDE')


class DoctoratCLSMFactory(_DoctoratFactory):
    entite_ucl_id = factory.SubFactory(UclEntityIdentityFactory, code='CLSM')


class DoctoratCDSCFactory(_DoctoratFactory):
    entite_ucl_id = factory.SubFactory(UclEntityIdentityFactory, code='CDSC')


class DoctoratCDSSDPFactory(_DoctoratFactory):
    entite_ucl_id = factory.SubFactory(UclEntityIdentityFactory, code='CDSS')
