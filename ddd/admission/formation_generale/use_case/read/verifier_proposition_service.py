# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.domain.service.i_maximum_propositions import IMaximumPropositionsAutorisees
from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.enums.question_specifique import Onglets
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from ddd.logic.shared_kernel.profil.repository.i_profil import IProfilRepository
from ...commands import VerifierPropositionQuery
from ...domain.builder.proposition_identity_builder import PropositionIdentityBuilder
from ...domain.model.proposition import PropositionIdentity
from ...domain.service.i_formation import IFormationGeneraleTranslator
from ...domain.service.i_question_specifique import IQuestionSpecifiqueTranslator
from ...domain.service.verifier_proposition import VerifierProposition
from ...repository.i_proposition import IPropositionRepository


def verifier_proposition(
    cmd: 'VerifierPropositionQuery',
    proposition_repository: 'IPropositionRepository',
    formation_translator: 'IFormationGeneraleTranslator',
    titres_acces: 'ITitresAcces',
    profil_candidat_translator: 'IProfilRepository',
    calendrier_inscription: 'ICalendrierInscription',
    academic_year_repository: 'IAcademicYearRepository',
    questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
    maximum_propositions_service: 'IMaximumPropositionsAutorisees',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )
    questions_specifiques = questions_specifiques_translator.search_by_proposition(
        cmd.uuid_proposition,
        onglets=Onglets.get_names(),
    )

    formation = formation_translator.get(proposition.formation_id)
    titres = titres_acces.recuperer_titres_access(
        proposition.matricule_candidat,
        formation.type,
        proposition.equivalence_diplome,
    )

    # WHEN
    VerifierProposition.verifier(
        proposition_candidat=proposition,
        formation_translator=formation_translator,
        titres_acces=titres_acces,
        profil_candidat_translator=profil_candidat_translator,
        calendrier_inscription=calendrier_inscription,
        annee_courante=annee_courante,
        questions_specifiques=questions_specifiques,
        maximum_propositions_service=maximum_propositions_service,
        titres=titres,
        formation=formation,
    )

    # THEN
    return proposition_id
