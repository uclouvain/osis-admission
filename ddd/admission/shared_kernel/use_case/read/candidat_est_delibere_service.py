# ##############################################################################
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
# ##############################################################################
from admission.ddd.admission.shared_kernel.commands import CandidatEstDelibereQuery
from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_ucl_candidat import (
    IInscriptionsUCLCandidatService,
)


def candidat_est_delibere(
    cmd: CandidatEstDelibereQuery,
    inscriptions_ucl_candidat_service: IInscriptionsUCLCandidatService,
    annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
):
    return inscriptions_ucl_candidat_service.est_delibere(
        matricule_candidat=cmd.matricule_candidat,
        annee_inscription_formation_translator=annee_inscription_formation_translator,
    )
