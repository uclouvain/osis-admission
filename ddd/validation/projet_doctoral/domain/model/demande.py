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
import datetime
from typing import List, Optional

import attr

from admission.ddd.preparation.projet_doctoral.domain.model._enums import ChoixStatutProposition, ChoixTypeAdmission
from admission.ddd.preparation.projet_doctoral.domain.model.doctorat import DoctoratIdentity
from admission.ddd.validation.projet_doctoral.domain.model._enums import ChoixStatutCDD, ChoixStatutSIC
from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class DemandeIdentity(interface.EntityIdentity):
    uuid = attr.ib(type=str)


@attr.s(slots=True, hash=False, eq=False)
class Demande(interface.RootEntity):
    entity_id = attr.ib(type=DemandeIdentity)
    type_admission = attr.ib(type=ChoixTypeAdmission)
    doctorat_id = attr.ib(type=DoctoratIdentity)
    matricule_candidat = attr.ib(type=str)
    reference = attr.ib(type=str)
    justification = attr.ib(type=Optional[str], default='')
    statut = attr.ib(type=ChoixStatutProposition, default=ChoixStatutProposition.IN_PROGRESS)
    statut_cdd = attr.ib(type=ChoixStatutCDD, default=ChoixStatutCDD.TO_BE_VERIFIED)
    statut_sic = attr.ib(type=ChoixStatutSIC, default=ChoixStatutSIC.TO_BE_VERIFIED)
    matricule_gestionnaire = attr.ib(type=Optional[str], default='')
    # commission_proximite = attr.ib(
    #     type=Optional[Union[ChoixCommissionProximiteCDEouCLSM, ChoixCommissionProximiteCDSS]], default=None
    # )
    onglets_ouverts = attr.ib(type=List[str], factory=list)
    creee_le = attr.ib(type=Optional[datetime.datetime], default=None)
    modifiee_le = attr.ib(type=Optional[datetime.datetime], default=None)
    confirmee_le = attr.ib(type=Optional[datetime.datetime], default=None)
    pre_admission_acceptee_le = attr.ib(type=Optional[datetime.datetime], default=None)
    admission_acceptee_le = attr.ib(type=Optional[datetime.datetime], default=None)
