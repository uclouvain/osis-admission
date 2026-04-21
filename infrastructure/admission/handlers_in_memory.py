##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from admission.ddd.admission.shared_kernel.commands import *
from admission.ddd.admission.shared_kernel.commands import RecupererInformationsDestinataireQuery
from admission.ddd.admission.shared_kernel.use_case.read import *
from admission.ddd.admission.shared_kernel.use_case.write import specifier_experience_en_tant_que_titre_acces
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.lister_toutes_demandes import (
    ListerToutesDemandesInMemory,
)
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.admission.shared_kernel.repository.in_memory.email_destinataire import (
    EmailDestinataireInMemoryRepository,
)
from admission.infrastructure.admission.shared_kernel.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.admission.shared_kernel.repository.in_memory.gestionnaire import (
    GestionnaireInMemoryRepository,
)
from admission.infrastructure.admission.shared_kernel.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepository,
)
from ddd.logic.shared_kernel.profil.queries import (
    RecupererInformationsValidationEtudesSecondairesQuery,
    RecupererInformationsValidationExamenQuery,
    RecupererInformationsValidationExperienceAcademiqueQuery,
    RecupererInformationsValidationExperienceNonAcademiqueQuery,
)
from infrastructure.shared_kernel.profil.domain.service.in_memory.parcours_interne import (
    ExperienceParcoursInterneInMemoryTranslator,
)

from .shared_kernel.domain.service.in_memory.annee_inscription_formation import (
    AnneeInscriptionFormationInMemoryTranslator,
)
from .shared_kernel.domain.service.in_memory.deliberation_translator import DeliberationInMemoryTranslator
from .shared_kernel.domain.service.in_memory.diffusion_notes_translator import DiffusionNotesInMemoryTranslator
from .shared_kernel.domain.service.in_memory.formation_translator import BaseFormationInMemoryTranslator
from .shared_kernel.domain.service.in_memory.inscriptions_evaluations_translator import (
    InscriptionsEvaluationsInMemoryTranslator,
)
from .shared_kernel.domain.service.in_memory.inscriptions_translator import InscriptionsInMemoryTranslator
from .shared_kernel.domain.service.in_memory.modifier_checklist_experience_parcours_anterieur import (
    ValidationExperienceParcoursAnterieurInMemoryService,
)

_emplacement_document_repository = emplacement_document_in_memory_repository
_profil_candidat_translator = ProfilCandidatInMemoryTranslator()
_titre_acces_selectionnable_repository = TitreAccesSelectionnableInMemoryRepository()
_experience_parcours_interne_translator = ExperienceParcoursInterneInMemoryTranslator()
_gestionnaire_repository = GestionnaireInMemoryRepository()
_validation_experience_parcours_anterieur = ValidationExperienceParcoursAnterieurInMemoryService()
_annee_inscription_formation_translator = AnneeInscriptionFormationInMemoryTranslator()
_inscriptions_translator = InscriptionsInMemoryTranslator()
_deliberation_translator = DeliberationInMemoryTranslator()
_base_formation_translator = BaseFormationInMemoryTranslator()
_diffusion_notes_translator = DiffusionNotesInMemoryTranslator()
_inscriptions_evaluations_translator = InscriptionsEvaluationsInMemoryTranslator()


COMMAND_HANDLERS = {
    ListerToutesDemandesQuery: lambda msg_bus, cmd: lister_demandes(
        cmd,
        lister_toutes_demandes_service=ListerToutesDemandesInMemory(),
    ),
    RecupererInformationsDestinataireQuery: lambda msg_bus, query: recuperer_informations_destinataire(
        query,
        email_destinataire_repository=EmailDestinataireInMemoryRepository(),
    ),
    RecupererEtudesSecondairesQuery: lambda msg_bus, query: recuperer_etudes_secondaires(
        query,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    RecupererExperienceAcademiqueQuery: lambda msg_bus, query: recuperer_experience_academique(
        query,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    RecupererExperienceNonAcademiqueQuery: lambda msg_bus, query: recuperer_experience_non_academique(
        query,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    RecupererConnaissancesLanguesQuery: lambda msg_bus, query: recuperer_connaissances_langues(
        query,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    RecupererTitresAccesSelectionnablesPropositionQuery: (
        lambda msg_bus, query: recuperer_titres_acces_selectionnables_proposition(
            query,
            titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
            experience_parcours_interne_translator=_experience_parcours_interne_translator,
        )
    ),
    SpecifierExperienceEnTantQueTitreAccesCommand: lambda msg_bus, cmd: specifier_experience_en_tant_que_titre_acces(
        msg_bus,
        cmd,
        titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
    ),
    RechercherFormationsGereesQuery: lambda msg_bus, cmd: rechercher_formations_gerees(
        cmd,
        repository=_gestionnaire_repository,
    ),
    RecupererInformationsValidationExperienceAcademiqueQuery: (
        lambda msg_bus, cmd: recuperer_informations_validation_experience_academique(
            cmd,
            validation_experience_parcours_anterieur_service=_validation_experience_parcours_anterieur,
        )
    ),
    RecupererInformationsValidationExperienceNonAcademiqueQuery: (
        lambda msg_bus, cmd: recuperer_informations_validation_experience_non_academique(
            cmd,
            validation_experience_parcours_anterieur_service=_validation_experience_parcours_anterieur,
        )
    ),
    RecupererInformationsValidationExamenQuery: (
        lambda msg_bus, cmd: recuperer_informations_validation_examen(
            cmd,
            validation_experience_parcours_anterieur_service=_validation_experience_parcours_anterieur,
        )
    ),
    RecupererInformationsValidationEtudesSecondairesQuery: (
        lambda msg_bus, cmd: recuperer_informations_validation_etudes_secondaires(
            cmd,
            validation_experience_parcours_anterieur_service=_validation_experience_parcours_anterieur,
        )
    ),
    RecupererInscriptionsCandidatQuery: lambda msg_bus, cmd: recuperer_inscriptions_candidat(
        cmd,
        inscriptions_translator=_inscriptions_translator,
        deliberation_translator=_deliberation_translator,
        formation_translator=_base_formation_translator,
    ),
    CandidatEstInscritRecemmentUCLQuery: lambda msg_bus, cmd: candidat_est_inscrit_recemment_ucl(
        cmd,
        annee_inscription_formation_translator=_annee_inscription_formation_translator,
        inscriptions_translator=_inscriptions_translator,
    ),
    CandidatEstEligibleALaReinscriptionQuery: lambda msg_bus, cmd: candidat_est_eligible_a_la_reinscription(
        cmd,
        annee_inscription_formation_translator=_annee_inscription_formation_translator,
        inscriptions_translator=_inscriptions_translator,
        deliberation_translator=_deliberation_translator,
        diffusion_notes_translator=_diffusion_notes_translator,
        inscriptions_evaluations_translator=_inscriptions_evaluations_translator,
    ),
    RecupererPeriodeReinscriptionQuery: lambda msg_bus, cmd: recuperer_periode_reinscription(
        cmd,
        annee_inscription_formation_translator=_annee_inscription_formation_translator,
        deliberation_translator=_deliberation_translator,
    ),
}
