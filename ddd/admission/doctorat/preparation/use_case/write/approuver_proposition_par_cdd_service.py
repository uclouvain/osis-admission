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

from admission.ddd.admission.doctorat.preparation.commands import (
    ApprouverPropositionParCddCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.groupe_de_supervision_dto import (
    GroupeDeSupervisionDto,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import (
    IHistorique,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_membre_CA import (
    IMembreCATranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import (
    INotification,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_pdf_generation import (
    IPDFGeneration,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import (
    IPromoteurTranslator,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.shared_kernel.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.shared_kernel.domain.repository.i_titre_acces_selectionnable import (
    ITitreAccesSelectionnableRepository,
)
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_unites_enseignement_translator import (
    IUnitesEnseignementTranslator,
)
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import (
    GetCurrentAcademicYear,
)
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import (
    IAcademicYearRepository,
)
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import (
    IPersonneConnueUclTranslator,
)
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import (
    IExperienceParcoursInterneTranslator,
)


def approuver_proposition_par_cdd(
    cmd: ApprouverPropositionParCddCommand,
    proposition_repository: 'IPropositionRepository',
    historique: 'IHistorique',
    pdf_generation: 'IPDFGeneration',
    personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
    unites_enseignement_translator: 'IUnitesEnseignementTranslator',
    titre_acces_selectionnable_repository: 'ITitreAccesSelectionnableRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    notification: 'INotification',
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

    groupe_supervision_dto = GroupeDeSupervisionDto().get(
        uuid_proposition=cmd.uuid_proposition,
        repository=groupe_supervision_repository,
    )

    titres_selectionnes = titre_acces_selectionnable_repository.search_by_proposition(
        proposition_identity=proposition.entity_id,
        experience_parcours_interne_translator=experience_parcours_interne_translator,
        seulement_selectionnes=True,
    )

    # WHEN
    proposition.approuver_par_cdd(
        auteur_modification=cmd.gestionnaire,
        titres_selectionnes=titres_selectionnes,
    )

    # THEN
    gestionnaire_dto = personne_connue_ucl_translator.get(cmd.gestionnaire)
    pdf_generation.generer_attestation_accord_cdd(
        proposition=proposition,
        gestionnaire=gestionnaire_dto,
        proposition_repository=proposition_repository,
        unites_enseignement_translator=unites_enseignement_translator,
        profil_candidat_translator=profil_candidat_translator,
        titres_selectionnes=titres_selectionnes,
        annee_courante=annee_courante,
        experience_parcours_interne_translator=experience_parcours_interne_translator,
        groupe_supervision_dto=groupe_supervision_dto,
    )

    proposition_repository.save(entity=proposition)

    message = notification.envoyer_message_libre_au_candidat(
        proposition=proposition,
        objet_message=cmd.objet_message,
        corps_message=cmd.corps_message,
        matricule_emetteur=cmd.gestionnaire,
        cc_promoteurs=True,
        cc_membres_ca=True,
    )

    historique.historiser_acceptation_cdd(proposition=proposition, gestionnaire=gestionnaire_dto, message=message)

    return proposition.entity_id
