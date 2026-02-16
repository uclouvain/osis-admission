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
from django.conf import settings

from admission.ddd.admission.formation_continue.event_handler import (
    GenererDocumentAnalysePropositionAutorisationHandler,
)
from admission.ddd.admission.shared_kernel.commands import *
from admission.ddd.admission.shared_kernel.commands import (
    RecupererInformationsDestinataireQuery,
)
from admission.ddd.admission.shared_kernel.use_case.read import *
from admission.ddd.admission.shared_kernel.use_case.write import (
    specifier_experience_en_tant_que_titre_acces,
)
from admission.infrastructure.admission.shared_kernel.domain.service.lister_toutes_demandes import (
    ListerToutesDemandes,
)
from admission.infrastructure.admission.shared_kernel.domain.service.profil_candidat import (
    ProfilCandidatTranslator,
)
from admission.infrastructure.admission.shared_kernel.repository.email_destinataire import (
    EmailDestinataireRepository,
)
from admission.infrastructure.admission.shared_kernel.repository.gestionnaire import (
    GestionnaireRepository,
)
from admission.infrastructure.admission.shared_kernel.repository.titre_acces_selectionnable import (
    TitreAccesSelectionnableRepository,
)
from infrastructure.shared_kernel.profil.domain.service.parcours_interne import (
    ExperienceParcoursInterneTranslator,
)
from osis_common.ddd.interface import EventConsumptionMode

COMMAND_HANDLERS = {
    ListerToutesDemandesQuery: lambda msg_bus, cmd: lister_demandes(
        cmd,
        lister_toutes_demandes_service=ListerToutesDemandes(),
    ),
    RecupererInformationsDestinataireQuery: lambda msg_bus, query: recuperer_informations_destinataire(
        query,
        email_destinataire_repository=EmailDestinataireRepository(),
    ),
    RecupererEtudesSecondairesQuery: lambda msg_bus, query: recuperer_etudes_secondaires(
        query,
        profil_candidat_translator=ProfilCandidatTranslator(),
    ),
    RecupererExperienceAcademiqueQuery: lambda msg_bus, query: recuperer_experience_academique(
        query,
        profil_candidat_translator=ProfilCandidatTranslator(),
    ),
    RecupererExperienceNonAcademiqueQuery: lambda msg_bus, query: recuperer_experience_non_academique(
        query,
        profil_candidat_translator=ProfilCandidatTranslator(),
    ),
    RecupererConnaissancesLanguesQuery: lambda msg_bus, query: recuperer_connaissances_langues(
        query,
        profil_candidat_translator=ProfilCandidatTranslator(),
    ),
    RecupererTitresAccesSelectionnablesPropositionQuery: (
        lambda msg_bus, query: recuperer_titres_acces_selectionnables_proposition(
            query,
            titre_acces_selectionnable_repository=TitreAccesSelectionnableRepository(),
            experience_parcours_interne_translator=ExperienceParcoursInterneTranslator(),
        )
    ),
    SpecifierExperienceEnTantQueTitreAccesCommand: lambda msg_bus, cmd: specifier_experience_en_tant_que_titre_acces(
        cmd,
        titre_acces_selectionnable_repository=TitreAccesSelectionnableRepository(),
        experience_parcours_interne_translator=ExperienceParcoursInterneTranslator(),
    ),
    RechercherFormationsGereesQuery: lambda msg_bus, cmd: rechercher_formations_gerees(
        cmd,
        repository=GestionnaireRepository(),
    ),
}

EVENT_HANDLERS = {}

if 'admission' in settings.INSTALLED_APPS:
    from admission.ddd.admission.doctorat.events import (
        AdmissionDoctoraleApprouveeParSicEvent,
        InscriptionDoctoraleApprouveeParSicEvent,
    )
    from admission.ddd.admission.formation_continue.events import (
        PropositionFormationContinueValideeEvent,
    )
    from admission.ddd.admission.formation_generale.events import (
        AdmissionApprouveeParSicEvent,
        InscriptionApprouveeParSicEvent,
    )
    from admission.infrastructure.admission.event_handler.reagir_a_approuver_proposition import (
        reagir_a_approuver_proposition,
    )

    EVENT_HANDLERS = {
        **EVENT_HANDLERS,
        InscriptionApprouveeParSicEvent: [reagir_a_approuver_proposition],
        AdmissionApprouveeParSicEvent: [reagir_a_approuver_proposition],
        InscriptionDoctoraleApprouveeParSicEvent: [reagir_a_approuver_proposition],
        AdmissionDoctoraleApprouveeParSicEvent: [reagir_a_approuver_proposition],
        PropositionFormationContinueValideeEvent: [
            GenererDocumentAnalysePropositionAutorisationHandler(consumption_mode=EventConsumptionMode.ASYNCHRONOUS),
        ],
    }
