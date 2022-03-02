# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
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

from admission.ddd.projet_doctoral.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.projet_doctoral.preparation.commands import SoumettrePropositionCommand
from admission.ddd.projet_doctoral.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.projet_doctoral.preparation.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.projet_doctoral.preparation.domain.service.verifier_proposition import VerifierProposition
from admission.ddd.projet_doctoral.preparation.repository.i_groupe_de_supervision import IGroupeDeSupervisionRepository
from admission.ddd.projet_doctoral.preparation.repository.i_proposition import IPropositionRepository
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository


def soumettre_proposition(
    cmd: 'SoumettrePropositionCommand',
    proposition_repository: 'IPropositionRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    academic_year_repository: 'IAcademicYearRepository',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)
    groupe_supervision = groupe_supervision_repository.get_by_proposition_id(proposition_id)
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )

    # WHEN
    VerifierProposition().verifier(proposition, groupe_supervision, profil_candidat_translator, annee_courante)

    # THEN
    proposition.finaliser()
    proposition_repository.save(proposition)

    return proposition_id
