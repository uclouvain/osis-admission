# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    DemanderSignaturesCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import (
    IHistorique,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import (
    INotification,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import (
    IPromoteurTranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.verifier_projet_doctoral import (
    VerifierPropositionProjetDoctoral,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.domain.service.i_raccrocher_experiences_curriculum import (
    IRaccrocherExperiencesCurriculum,
)
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import (
    GetCurrentAcademicYear,
)
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import (
    IAcademicYearRepository,
)


def demander_signatures(
    cmd: 'DemanderSignaturesCommand',
    proposition_repository: 'IPropositionRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    historique: 'IHistorique',
    notification: 'INotification',
    academic_year_repository: 'IAcademicYearRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    raccrocher_experiences_curriculum: 'IRaccrocherExperiencesCurriculum',
) -> 'PropositionIdentity':
    # GIVEN
    entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_candidat = proposition_repository.get(entity_id=entity_id)
    groupe_de_supervision = groupe_supervision_repository.get_by_proposition_id(entity_id)
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )
    VerifierPropositionProjetDoctoral.verifier(
        proposition_candidat=proposition_candidat,
        groupe_de_supervision=groupe_de_supervision,
        questions_specifiques=[],
        promoteur_translator=promoteur_translator,
        annee_courante=annee_courante,
        profil_candidat_translator=profil_candidat_translator,
    )

    # WHEN
    proposition_candidat.verrouiller_proposition_pour_signature()
    groupe_de_supervision.verrouiller_groupe_pour_signature()
    groupe_de_supervision.inviter_a_signer()

    # THEN
    groupe_supervision_repository.save(groupe_de_supervision)
    proposition_repository.save(proposition_candidat)
    raccrocher_experiences_curriculum.raccrocher(proposition_candidat)
    notification.envoyer_signatures(proposition_candidat, groupe_de_supervision)
    historique.historiser_demande_signatures(proposition_candidat, cmd.matricule_auteur)

    return proposition_candidat.entity_id
