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
import datetime

from admission.ddd.admission.formation_generale.commands import (
    ModifierStatutChecklistParcoursAnterieurCommand,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_generale.domain.service.i_formation import (
    IFormationGeneraleTranslator,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.shared_kernel.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.ddd.admission.shared_kernel.repository.i_titre_acces_selectionnable import (
    ITitreAccesSelectionnableRepository,
)
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import (
    IExperienceParcoursInterneTranslator,
)


def modifier_statut_checklist_parcours_anterieur(
    cmd: 'ModifierStatutChecklistParcoursAnterieurCommand',
    proposition_repository: 'IPropositionRepository',
    titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
    experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
    profil_candidat_translator: 'IProfilCandidatTranslator',
    formation_translator: 'IFormationGeneraleTranslator',
    academic_year_repository: 'IAcademicYearRepository',
) -> 'PropositionIdentity':
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )

    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)
    formation = formation_translator.get(entity_id=proposition.formation_id)

    titres_acces_selectionnes = titre_acces_selectionnable_repository.search_by_proposition(
        proposition_identity=proposition_id,
        experience_parcours_interne_translator=experience_parcours_interne_translator,
        seulement_selectionnes=True,
    )

    etudes_secondaires = profil_candidat_translator.get_etudes_secondaires(matricule=proposition.matricule_candidat)

    curriculum = profil_candidat_translator.get_curriculum(
        matricule=proposition.matricule_candidat,
        experiences_cv_recuperees=ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION,
        uuid_proposition=proposition.entity_id.uuid,
        annee_courante=annee_courante,
    )

    examen = profil_candidat_translator.get_examen(
        uuid_proposition=proposition.entity_id.uuid,
        matricule=proposition.matricule_candidat,
        formation_sigle=proposition.formation_id.sigle,
        formation_annee=proposition.formation_id.annee,
    )

    proposition.specifier_statut_checklist_parcours_anterieur(
        statut_checklist_cible=cmd.statut,
        titres_acces_selectionnes=titres_acces_selectionnes,
        auteur_modification=cmd.gestionnaire,
        type_formation=formation.type,
        etudes_secondaires=etudes_secondaires,
        examen=examen,
        experiences_academiques=curriculum.experiences_academiques,
        experiences_non_academiques=curriculum.experiences_non_academiques,
    )

    proposition_repository.save(proposition)

    return proposition_id
