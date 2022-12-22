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

from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.profil_candidat import ProfilCandidat
from admission.ddd.admission.formation_generale.commands import VerifierCurriculumQuery
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from ...domain.builder.proposition_identity_builder import PropositionIdentityBuilder
from ...domain.model.proposition import PropositionIdentity
from ...domain.service.i_formation import IFormationGeneraleTranslator
from ...repository.i_proposition import IPropositionRepository


def verifier_curriculum(
    cmd: 'VerifierCurriculumQuery',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    formation_translator: 'IFormationGeneraleTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)
    formation = formation_translator.get(proposition.formation_id)
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )

    # WHEN
    ProfilCandidat().verifier_curriculum_formation_generale(
        proposition=proposition,
        type_formation=formation.type,
        profil_candidat_translator=profil_candidat_translator,
        annee_courante=annee_courante,
    )

    # THEN
    return proposition_id
