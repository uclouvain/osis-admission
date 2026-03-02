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
from admission.ddd.admission.shared_kernel.commands import CandidatEstEligibleALaReinscriptionQuery
from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_diffusion_notes_translator import IDiffusionNotesTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_evaluations_translator import (
    IInscriptionsEvaluationsTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.domain.service.inscriptions_ucl_candidat import (
    InscriptionsUCLCandidatService,
)


def candidat_est_eligible_a_la_reinscription(
    cmd: CandidatEstEligibleALaReinscriptionQuery,
    annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    inscriptions_translator: IInscriptionsTranslatorService,
    deliberation_translator: IDeliberationTranslator,
    diffusion_notes_translator: IDiffusionNotesTranslator,
    inscriptions_evaluations_translator: IInscriptionsEvaluationsTranslator,
):
    return InscriptionsUCLCandidatService.est_eligible_a_la_reinscription(
        matricule_candidat=cmd.matricule_candidat,
        annee_inscription_formation_translator=annee_inscription_formation_translator,
        inscriptions_translator=inscriptions_translator,
        deliberation_translator=deliberation_translator,
        diffusion_notes_translator=diffusion_notes_translator,
        inscriptions_evaluations_translator=inscriptions_evaluations_translator,
    )
