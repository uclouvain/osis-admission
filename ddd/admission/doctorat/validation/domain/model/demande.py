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

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.admission.doctorat.validation.domain.validator.validator_by_business_action import (
    ApprouverDemandeCDDValidatorList,
    RefuserDemandeCDDValidatorList,
)
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class DemandeIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Demande(interface.RootEntity):
    entity_id: DemandeIdentity
    proposition_id: PropositionIdentity
    profil_soumis_candidat: ProfilCandidat
    statut_cdd: ChoixStatutCDD = ChoixStatutCDD.TO_BE_VERIFIED
    statut_sic: ChoixStatutSIC = ChoixStatutSIC.TO_BE_VERIFIED
    matricule_gestionnaire: Optional[str] = ''
    onglets_ouverts: List[str] = attr.Factory(list)
    modifiee_le: Optional[datetime.datetime] = None
    pre_admission_confirmee_le: Optional[datetime.datetime] = None
    admission_confirmee_le: Optional[datetime.datetime] = None
    pre_admission_acceptee_le: Optional[datetime.datetime] = None
    admission_acceptee_le: Optional[datetime.datetime] = None

    def refuser_cdd(self) -> None:
        RefuserDemandeCDDValidatorList(self).validate()
        self.statut_cdd = ChoixStatutCDD.REJECTED

    def approuver_cdd(self) -> None:
        ApprouverDemandeCDDValidatorList(self).validate()
        self.statut_cdd = ChoixStatutCDD.ACCEPTED
