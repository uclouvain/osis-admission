# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.doctorat.preparation.commands import (
    SpecifierMotifsRefusPropositionParCDDCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)


def specifier_motifs_refus_proposition_par_cdd(
    cmd: SpecifierMotifsRefusPropositionParCDDCommand,
    proposition_repository: 'IPropositionRepository',
) -> PropositionIdentity:
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    proposition.specifier_motifs_refus_par_cdd(
        uuids_motifs=cmd.uuids_motifs,
        autres_motifs=cmd.autres_motifs,
        auteur_modification=cmd.gestionnaire,
    )

    proposition_repository.save(entity=proposition)

    return proposition.entity_id
