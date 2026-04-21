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

from admission.ddd.admission.shared_kernel.commands import RecupererInscriptionsCandidatQuery
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_formation_translator import IBaseFormationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.domain.service.inscriptions_ucl_candidat import (
    InscriptionsUCLCandidatService,
)


def recuperer_inscriptions_candidat(
    cmd: RecupererInscriptionsCandidatQuery,
    inscriptions_translator: IInscriptionsTranslatorService,
    formation_translator: IBaseFormationTranslator,
    deliberation_translator: IDeliberationTranslator,
):
    return InscriptionsUCLCandidatService.recuperer(
        matricule_candidat=cmd.matricule_candidat,
        annees=cmd.annees,
        inscriptions_translator=inscriptions_translator,
        formation_translator=formation_translator,
        deliberation_translator=deliberation_translator,
    )
