# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial

from admission.ddd.projet_doctoral.doctorat.commands import *
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import *
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.use_case.read import *
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.use_case.write import *
from admission.ddd.projet_doctoral.doctorat.use_case.read import *
from admission.ddd.projet_doctoral.preparation.commands import *
from admission.ddd.projet_doctoral.preparation.use_case.read import *
from admission.ddd.projet_doctoral.preparation.use_case.write import *
from admission.ddd.projet_doctoral.validation.commands import *
from admission.ddd.projet_doctoral.validation.use_case.read import *
from admission.ddd.projet_doctoral.validation.use_case.write import *
from admission.infrastructure.projet_doctoral.doctorat.repository.in_memory.doctorat import DoctoratInMemoryRepository
from admission.infrastructure.projet_doctoral.preparation.domain.service.in_memory.doctorat import (
    DoctoratInMemoryTranslator,
)
from admission.infrastructure.projet_doctoral.preparation.domain.service.in_memory.historique import HistoriqueInMemory
from admission.infrastructure.projet_doctoral.preparation.domain.service.in_memory.membre_CA import (
    MembreCAInMemoryTranslator,
)
from admission.infrastructure.projet_doctoral.preparation.domain.service.in_memory.notification import (
    NotificationInMemory,
)
from admission.infrastructure.projet_doctoral.preparation.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.projet_doctoral.preparation.domain.service.in_memory.promoteur import (
    PromoteurInMemoryTranslator,
)
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.projet_doctoral.validation.repository.in_memory.demande import DemandeInMemoryRepository
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from infrastructure.utils import AbstractMessageBusCommands, MessageBus
from .projet_doctoral.doctorat.epreuve_confirmation.repository.in_memory.epreuve_confirmation import (
    EpreuveConfirmationInMemoryRepository,
)


class MessageBusInMemoryCommands(AbstractMessageBusCommands):
    command_handlers = {
        InitierPropositionCommand: partial(
            initier_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            doctorat_translator=DoctoratInMemoryTranslator(),
            historique=HistoriqueInMemory(),
        ),
        RechercherDoctoratCommand: partial(
            rechercher_doctorats,
            doctorat_translator=DoctoratInMemoryTranslator(),
        ),
        CompleterPropositionCommand: partial(
            completer_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            doctorat_translator=DoctoratInMemoryTranslator(),
            historique=HistoriqueInMemory(),
        ),
        GetPropositionCommand: partial(
            recuperer_proposition,
            proposition_repository=PropositionInMemoryRepository(),
        ),
        DefinirCotutelleCommand: partial(
            definir_cotutelle,
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            proposition_repository=PropositionInMemoryRepository(),
            historique=HistoriqueInMemory(),
        ),
        GetCotutelleCommand: partial(
            recuperer_cotutelle,
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        ),
        IdentifierPromoteurCommand: partial(
            identifier_promoteur,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            promoteur_translator=PromoteurInMemoryTranslator(),
            historique=HistoriqueInMemory(),
        ),
        IdentifierMembreCACommand: partial(
            identifier_membre_CA,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            membre_CA_translator=MembreCAInMemoryTranslator(),
            historique=HistoriqueInMemory(),
        ),
        GetGroupeDeSupervisionCommand: partial(
            recuperer_groupe_de_supervision,
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            promoteur_translator=PromoteurInMemoryTranslator(),
            membre_ca_translator=MembreCAInMemoryTranslator(),
        ),
        SupprimerPromoteurCommand: partial(
            supprimer_promoteur,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            historique=HistoriqueInMemory(),
            notification=NotificationInMemory(),
        ),
        SupprimerMembreCACommand: partial(
            supprimer_membre_CA,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            historique=HistoriqueInMemory(),
            notification=NotificationInMemory(),
        ),
        DemanderSignaturesCommand: partial(
            demander_signatures,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            promoteur_translator=PromoteurInMemoryTranslator(),
            historique=HistoriqueInMemory(),
            notification=NotificationInMemory(),
        ),
        VerifierProjetCommand: partial(
            verifier_projet,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            promoteur_translator=PromoteurInMemoryTranslator(),
        ),
        VerifierPropositionCommand: partial(
            verifier_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            profil_candidat_translator=ProfilCandidatInMemoryTranslator(),
            academic_year_repository=AcademicYearInMemoryRepository(),
        ),
        SoumettrePropositionCommand: partial(
            soumettre_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            demande_repository=DemandeInMemoryRepository(),
            profil_candidat_translator=ProfilCandidatInMemoryTranslator(),
            academic_year_repository=AcademicYearInMemoryRepository(),
            historique=HistoriqueInMemory(),
            notification=NotificationInMemory(),
        ),
        ApprouverPropositionCommand: partial(
            approuver_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            historique=HistoriqueInMemory(),
            notification=NotificationInMemory(),
        ),
        ApprouverPropositionParPdfCommand: partial(
            approuver_proposition_par_pdf,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            historique=HistoriqueInMemory(),
        ),
        RefuserPropositionCommand: partial(
            refuser_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            historique=HistoriqueInMemory(),
            notification=NotificationInMemory(),
        ),
        ListerPropositionsCandidatQuery: partial(
            lister_propositions_candidat,
            proposition_repository=PropositionInMemoryRepository(),
        ),
        ListerPropositionsSuperviseesQuery: partial(
            lister_propositions_supervisees,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        ),
        SupprimerPropositionCommand: partial(
            supprimer_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            historique=HistoriqueInMemory(),
        ),
        FiltrerDemandesQuery: partial(
            filtrer_demandes,
            proposition_repository=PropositionInMemoryRepository(),
            demande_repository=DemandeInMemoryRepository(),
        ),
        RecupererDemandeQuery: partial(
            recuperer_demande,
            demande_repository=DemandeInMemoryRepository(),
        ),
        ApprouverDemandeCddCommand: partial(
            approuver_demande_cdd,
            demande_repository=DemandeInMemoryRepository(),
            proposition_repository=PropositionInMemoryRepository(),
            epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
            doctorat_repository=DoctoratInMemoryRepository(),
        ),
        RecupererEpreuvesConfirmationQuery: partial(
            recuperer_epreuves_confirmation_service,
            epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
            doctorat_repository=DoctoratInMemoryRepository(),
        ),
        RecupererDerniereEpreuveConfirmationQuery: partial(
            recuperer_dernierer_epreuve_confirmation_service,
            epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
            doctorat_repository=DoctoratInMemoryRepository(),
        ),
        ModifierEpreuveConfirmationParCDDCommand: partial(
            modifier_epreuve_confirmation_par_cdd_service,
            epreuve_confirmation_repository=EpreuveConfirmationInMemoryRepository(),
        ),
        RecupererDoctoratQuery: partial(
            recuperer_doctorat_service,
            doctorat_repository=DoctoratInMemoryRepository(),
        ),
    }


message_bus_in_memory_instance = MessageBus(MessageBusInMemoryCommands.get_command_handlers())
