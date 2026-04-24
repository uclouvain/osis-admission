# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from datetime import timedelta

from attr import dataclass
from django.utils.formats import date_format
from django.utils.translation import gettext

from admission.ddd.admission.shared_kernel.domain.model.enums.eligibilite_reinscription import EligibiliteReinscription
from base.utils.utils import format_academic_year
from osis_common.ddd.interface import DTO


@dataclass(frozen=True, slots=True)
class EligibiliteReinscriptionDTO(DTO):
    decision: str
    raison_non_eligibilite: str = ''

    @classmethod
    def est_eligible(cls):
        return EligibiliteReinscriptionDTO(decision=EligibiliteReinscription.EST_ELIGIBLE.name)

    @classmethod
    def est_non_eligible_et_en_attente_resultats(cls, annee: int):
        return EligibiliteReinscriptionDTO(
            decision=EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name,
            raison_non_eligibilite=gettext('Waiting for all your results for the %(academic_year)s academic year.')
            % {'academic_year': format_academic_year(year=annee)},
        )

    @classmethod
    def est_non_eligible_et_en_attente_fin_periode_inscription_examens(cls, date_fin_periode_inscription_examens):
        return EligibiliteReinscriptionDTO(
            decision=EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_FIN_INSCRIPTION_EXAMENS_SESSION_3.name,
            raison_non_eligibilite=gettext('Re-registration will be available from %(date)s.')
            % {'date': date_format(date_fin_periode_inscription_examens + timedelta(days=1), format='j F Y')},
        )
