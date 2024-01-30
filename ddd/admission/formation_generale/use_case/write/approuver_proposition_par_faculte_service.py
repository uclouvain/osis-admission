# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.repository.i_titre_acces_selectionnable import ITitreAccesSelectionnableRepository
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import IUnitesEnseignementTranslator
from admission.ddd.admission.formation_generale.commands import (
    ApprouverPropositionParFaculteCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.domain.service.i_pdf_generation import IPDFGeneration
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator


def approuver_proposition_par_faculte(
    cmd: ApprouverPropositionParFaculteCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
    pdf_generation: 'IPDFGeneration',
    personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
    unites_enseignement_translator: 'IUnitesEnseignementTranslator',
    titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    academic_year_repository: 'IAcademicYearRepository',
) -> PropositionIdentity:
    # GIVEN
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    titres_selectionnes = titre_acces_selectionnable_repository.search_by_proposition(
        proposition_identity=proposition.entity_id,
        seulement_selectionnes=True,
    )

    # WHEN
    proposition.approuver_par_fac(
        auteur_modification=cmd.gestionnaire,
        titres_selectionnes=titres_selectionnes,
    )

    # THEN
    gestionnaire_dto = personne_connue_ucl_translator.get(cmd.gestionnaire)
    pdf_generation.generer_attestation_accord_facultaire(
        proposition=proposition,
        gestionnaire=gestionnaire_dto,
        proposition_repository=proposition_repository,
        unites_enseignement_translator=unites_enseignement_translator,
        profil_candidat_translator=profil_candidat_translator,
        titres_selectionnes=titres_selectionnes,
        annee_courante=annee_courante,
    )

    proposition_repository.save(entity=proposition)

    historique.historiser_acceptation_fac(proposition=proposition, gestionnaire=gestionnaire_dto)

    return proposition.entity_id
