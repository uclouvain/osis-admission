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

from base.models.enums.entity_type import EntityType
from ddd.logic.shared_kernel.entite.tests.factory.entiteucl import _EntiteUCLFactory, _IdentiteEntiteFactory


class CDEEntiteFactory(_EntiteUCLFactory):
    entity_id = factory.SubFactory(_IdentiteEntiteFactory, sigle='CDE')
    parent = factory.SubFactory(_IdentiteEntiteFactory, sigle='SSH')
    type = EntityType.DOCTORAL_COMMISSION
    intitule = 'Commission doctorale du domaine "Sciences économiques et de gestion"'


class CDAEntiteFactory(_EntiteUCLFactory):
    entity_id = factory.SubFactory(_IdentiteEntiteFactory, sigle='CDA')
    parent = factory.SubFactory(_IdentiteEntiteFactory, sigle='SST')
    type = EntityType.DOCTORAL_COMMISSION
    intitule = 'Commission doctorale du domaine "sciences agronomiques et ingénierie biologique"'


class CDSCEntiteFactory(_EntiteUCLFactory):
    entity_id = factory.SubFactory(_IdentiteEntiteFactory, sigle='CDSC')
    parent = factory.SubFactory(_IdentiteEntiteFactory, sigle='SST')
    type = EntityType.DOCTORAL_COMMISSION
    intitule = 'Commission doctorale des domaines "Sciences et sciences vétérinaires"'


class SSHEntiteFactory(_EntiteUCLFactory):
    entity_id = factory.SubFactory(_IdentiteEntiteFactory, sigle='SSH')
    parent = factory.SubFactory(_IdentiteEntiteFactory, sigle='UCL')
    type = EntityType.SECTOR
    intitule = "Secteur des sciences humaines"
