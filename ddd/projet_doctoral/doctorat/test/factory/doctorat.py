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

from admission.ddd.projet_doctoral.doctorat.domain.model._formation import FormationIdentity
from admission.ddd.projet_doctoral.doctorat.domain.model.doctorat import DoctoratIdentity, Doctorat
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.preparation.domain.model._financement import BourseRecherche, ChoixTypeFinancement


class _DoctoratIdentityFactory(factory.Factory):
    class Meta:
        model = DoctoratIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _DoctoratFactory(factory.Factory):
    class Meta:
        model = Doctorat
        abstract = False

    entity_id = factory.SubFactory(_DoctoratIdentityFactory)
    statut = ChoixStatutDoctorat.ADMITTED


class DoctoratSC3DPMinimaleFactory(_DoctoratFactory):
    entity_id = factory.SubFactory(_DoctoratIdentityFactory, uuid='uuid-SC3DP')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '1'
    reference = 'r1'


class DoctoratPreSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(_DoctoratFactory):
    entity_id = factory.SubFactory(_DoctoratIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '1'
    reference = 'r2'


class DoctoratSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(_DoctoratFactory):
    entity_id = factory.SubFactory(_DoctoratIdentityFactory, uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '2'
    reference = 'r3'
    statut = ChoixStatutDoctorat.ADMISSION_IN_PROGRESS


class DoctoratSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(_DoctoratFactory):
    entity_id = factory.SubFactory(_DoctoratIdentityFactory, uuid='uuid-SC3DP-promoteurs-membres-deja-approuves')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '3'
    reference = 'r4'
