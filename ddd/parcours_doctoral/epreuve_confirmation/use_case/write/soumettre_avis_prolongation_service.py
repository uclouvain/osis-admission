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
from admission.ddd.parcours_doctoral.domain.model.doctorat import DoctoratIdentity
from admission.ddd.parcours_doctoral.epreuve_confirmation.builder.epreuve_confirmation_identity import (
    EpreuveConfirmationIdentityBuilder,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.commands import (
    SoumettreAvisProlongationCommand,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)


def soumettre_avis_prolongation(
    cmd: 'SoumettreAvisProlongationCommand',
    epreuve_confirmation_repository: 'IEpreuveConfirmationRepository',
) -> DoctoratIdentity:
    # GIVEN
    epreuve_confirmation_id = EpreuveConfirmationIdentityBuilder.build_from_uuid(cmd.uuid)
    epreuve_confirmation = epreuve_confirmation_repository.get(epreuve_confirmation_id)

    epreuve_confirmation.verifier_avis_prolongation(avis_cdd=cmd.avis_cdd)

    # WHEN
    epreuve_confirmation.soumettre_avis_prolongation(avis_cdd=cmd.avis_cdd)

    # THEN
    epreuve_confirmation_repository.save(epreuve_confirmation)

    return epreuve_confirmation.doctorat_id
