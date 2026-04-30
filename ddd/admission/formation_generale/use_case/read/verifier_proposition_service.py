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
import datetime

from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_calendrier_inscription import (
    ICalendrierInscription,
)
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_diffusion_notes_translator import IDiffusionNotesTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_evaluations_translator import (
    IInscriptionsEvaluationsTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.domain.service.i_maximum_propositions import (
    IMaximumPropositionsAutorisees,
)
from admission.ddd.admission.shared_kernel.domain.service.i_noma_translator import INomasTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_titres_acces import (
    ITitresAcces,
)
from admission.ddd.admission.shared_kernel.domain.service.inscriptions_ucl_candidat import (
    InscriptionsUCLCandidatService,
)
from admission.ddd.admission.shared_kernel.enums.question_specifique import Onglets
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYearIdentity,
)
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import (
    GetCurrentAcademicYear,
)
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import (
    IAcademicYearRepository,
)

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
    profil_candidat_translator: 'IProfilCandidatTranslator',
    calendrier_inscription: 'ICalendrierInscription',
    academic_year_repository: 'IAcademicYearRepository',
    questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
    maximum_propositions_service: 'IMaximumPropositionsAutorisees',
    inscriptions_translator: IInscriptionsTranslatorService,
    deliberation_translator: IDeliberationTranslator,
    diffusion_notes_translator: IDiffusionNotesTranslator,
    inscriptions_evaluations_translator: IInscriptionsEvaluationsTranslator,
    annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    nomas_translator: INomasTranslator,
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
    annee_formation = academic_year_repository.get(
        entity_id=AcademicYearIdentity(year=proposition.annee_calculee or proposition.formation_id.annee)
    )

    questions_specifiques = questions_specifiques_translator.search_by_proposition(
        cmd.uuid_proposition,
        onglets=Onglets.get_names(),
    )

    inscriptions_ucl_candidat = InscriptionsUCLCandidatService.recuperer(
        matricule_candidat=proposition.matricule_candidat,
        inscriptions_translator=inscriptions_translator,
        formation_translator=formation_translator,
        deliberation_translator=deliberation_translator,
    )

    formation = formation_translator.get(proposition.formation_id)
    titres = titres_acces.recuperer_titres_access(
        matricule_candidat=proposition.matricule_candidat,
        type_formation=formation.type,
        equivalence_diplome=proposition.equivalence_diplome,
        inscriptions_ucl_candidat=inscriptions_ucl_candidat,
    )

    candidat_est_inscrit_recemment_ucl = inscriptions_translator.est_inscrit_recemment(
        matricule_candidat=proposition.matricule_candidat,
        annee_inscription_formation_translator=annee_inscription_formation_translator,
    )

    candidat_est_en_poursuite_directe = inscriptions_translator.est_en_poursuite_directe(
        matricule_candidat=proposition.matricule_candidat,
        sigle_formation=formation.entity_id.sigle,
        annee_inscription_formation_translator=annee_inscription_formation_translator,
    )

    assimilation_passee = inscriptions_translator.recuperer_assimilation_inscription_formation_annee_precedente(
        matricule_candidat=proposition.matricule_candidat,
        sigle_formation=proposition.formation_id.sigle,
        annee_inscription_formation_translator=annee_inscription_formation_translator,
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
        annee_formation=annee_formation,
        annee_inscription_formation_translator=annee_inscription_formation_translator,
        inscriptions_translator=inscriptions_translator,
        deliberation_translator=deliberation_translator,
        diffusion_notes_translator=diffusion_notes_translator,
        inscriptions_evaluations_translator=inscriptions_evaluations_translator,
        candidat_est_inscrit_recemment_ucl=candidat_est_inscrit_recemment_ucl,
        nomas_translator=nomas_translator,
        assimilation_passee=assimilation_passee,
        candidat_est_en_poursuite_directe=candidat_est_en_poursuite_directe,
        inscriptions_ucl_candidat=inscriptions_ucl_candidat,
    )

    # THEN
    return proposition_id
