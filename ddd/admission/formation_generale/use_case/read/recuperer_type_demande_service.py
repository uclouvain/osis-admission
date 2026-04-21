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

from admission.ddd.admission.formation_generale.commands import RecupererTypeDemandeQuery
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.service.i_formation import IFormationGeneraleTranslator
from admission.ddd.admission.formation_generale.domain.service.verifier_proposition import VerifierProposition
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.shared_kernel.domain.service.inscriptions_ucl_candidat import (
    InscriptionsUCLCandidatService,
)


def recuperer_type_demande(
    cmd: 'RecupererTypeDemandeQuery',
    proposition_repository: 'IPropositionRepository',
    formation_translator: 'IFormationGeneraleTranslator',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    titres_acces: 'ITitresAcces',
    calendrier_inscription: 'ICalendrierInscription',
    inscriptions_translator: IInscriptionsTranslatorService,
    annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    deliberation_translator: IDeliberationTranslator,
) -> str:
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    formation = formation_translator.get(proposition.formation_id)

    inscriptions_ucl_candidat = InscriptionsUCLCandidatService.recuperer(
        matricule_candidat=proposition.matricule_candidat,
        inscriptions_translator=inscriptions_translator,
        formation_translator=formation_translator,
        deliberation_translator=deliberation_translator,
    )

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

    type_demande = VerifierProposition.determiner_type_demande(
        proposition=proposition,
        titres=titres,
        calendrier_inscription=calendrier_inscription,
        profil_candidat_translator=profil_candidat_translator,
        candidat_est_inscrit_recemment_ucl=candidat_est_inscrit_recemment_ucl,
    )

    return type_demande.name
