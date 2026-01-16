##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.service.i_contingente import (
    IContingente,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)


class ContingenteInMemory(IContingente):
    @classmethod
    def generer_numero_de_dossier_ares_si_necessaire(cls, proposition: 'Proposition', annee: int) -> str:
        if proposition.formation_id.sigle in SIGLES_WITH_QUOTA and proposition.est_non_resident_au_sens_decret:
            return f"UCLouvain/{proposition.formation_id.sigle[0]}-{str(annee)[-2:]}0001"
        return ""

    @classmethod
    def verifier_proposition_contingente_unique(cls, proposition_candidat: 'PropositionFormationGenerale'):
        pass
