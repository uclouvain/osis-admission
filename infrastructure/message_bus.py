##############################################################################
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
##############################################################################
from functools import partial

from admission.ddd.projet_doctoral.preparation.commands import *
from admission.ddd.projet_doctoral.preparation.use_case.read import *
from admission.ddd.projet_doctoral.preparation.use_case.write import *
from admission.ddd.projet_doctoral.validation.commands import *
from admission.ddd.projet_doctoral.validation.use_case.read import *
from admission.ddd.projet_doctoral.validation.use_case.write import *
from admission.infrastructure.projet_doctoral.doctorat.epreuve_confirmation.repository.epreuve_confirmation import (
    EpreuveConfirmationRepository,
)
from admission.infrastructure.projet_doctoral.doctorat.repository.doctorat import DoctoratRepository
from admission.infrastructure.projet_doctoral.preparation.domain.service.doctorat import DoctoratTranslator
from admission.infrastructure.projet_doctoral.preparation.domain.service.historique import Historique
from admission.infrastructure.projet_doctoral.preparation.domain.service.membre_CA import MembreCATranslator
from admission.infrastructure.projet_doctoral.preparation.domain.service.notification import Notification
from admission.infrastructure.projet_doctoral.preparation.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.infrastructure.projet_doctoral.preparation.domain.service.promoteur import PromoteurTranslator
from admission.infrastructure.projet_doctoral.preparation.repository.groupe_de_supervision import (
    GroupeDeSupervisionRepository,
)
from admission.infrastructure.projet_doctoral.preparation.repository.proposition import PropositionRepository
from admission.infrastructure.projet_doctoral.validation.repository.demande import DemandeRepository
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from infrastructure.utils import AbstractMessageBusCommands


class MessageBusCommands(AbstractMessageBusCommands):
    command_handlers = {
        InitierPropositionCommand: partial(
            initier_proposition,
            proposition_repository=PropositionRepository(),
            doctorat_translator=DoctoratTranslator(),
            historique=Historique(),
        ),
        ListerPropositionsCandidatQuery: partial(
            lister_propositions_candidat,
            proposition_repository=PropositionRepository(),
        ),
        ListerPropositionsSuperviseesQuery: partial(
            lister_propositions_supervisees,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        GetPropositionCommand: partial(
            recuperer_proposition,
            proposition_repository=PropositionRepository(),
        ),
        CompleterPropositionCommand: partial(
            completer_proposition,
            proposition_repository=PropositionRepository(),
            doctorat_translator=DoctoratTranslator(),
            historique=Historique(),
        ),
        DefinirCotutelleCommand: partial(
            definir_cotutelle,
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            proposition_repository=PropositionRepository(),
            historique=Historique(),
        ),
        GetCotutelleCommand: partial(
            recuperer_cotutelle,
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        IdentifierPromoteurCommand: partial(
            identifier_promoteur,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
            historique=Historique(),
        ),
        IdentifierMembreCACommand: partial(
            identifier_membre_CA,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            membre_CA_translator=MembreCATranslator(),
            historique=Historique(),
        ),
        GetGroupeDeSupervisionCommand: partial(
            recuperer_groupe_de_supervision,
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
            membre_ca_translator=MembreCATranslator(),
        ),
        SupprimerPromoteurCommand: partial(
            supprimer_promoteur,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            historique=Historique(),
            notification=Notification(),
        ),
        SupprimerMembreCACommand: partial(
            supprimer_membre_CA,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            historique=Historique(),
            notification=Notification(),
        ),
        DemanderSignaturesCommand: partial(
            demander_signatures,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
            historique=Historique(),
            notification=Notification(),
        ),
        VerifierProjetCommand: partial(
            verifier_projet,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
        ),
        VerifierPropositionCommand: partial(
            verifier_proposition,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            profil_candidat_translator=ProfilCandidatTranslator(),
            academic_year_repository=AcademicYearRepository(),
        ),
        SoumettrePropositionCommand: partial(
            soumettre_proposition,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            demande_repository=DemandeRepository(),
            profil_candidat_translator=ProfilCandidatTranslator(),
            academic_year_repository=AcademicYearRepository(),
            historique=Historique(),
            notification=Notification(),
        ),
        ApprouverPropositionCommand: partial(
            approuver_proposition,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            historique=Historique(),
            notification=Notification(),
        ),
        ApprouverPropositionParPdfCommand: partial(
            approuver_proposition_par_pdf,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            historique=Historique(),
        ),
        RefuserPropositionCommand: partial(
            refuser_proposition,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            historique=Historique(),
            notification=Notification(),
        ),
        SearchDoctoratCommand: partial(
            rechercher_doctorats,
            doctorat_translator=DoctoratTranslator(),
        ),
        SupprimerPropositionCommand: partial(
            supprimer_proposition,
            proposition_repository=PropositionRepository(),
            historique=Historique(),
        ),
        FiltrerDemandesQuery: partial(
            filtrer_demandes,
            proposition_repository=PropositionRepository(),
            demande_repository=DemandeRepository(),
        ),
        RecupererDemandeQuery: partial(
            recuperer_demande,
            demande_repository=DemandeRepository(),
        ),
        ApprouverDemandeCddCommand: partial(
            approuver_demande_cdd,
            demande_repository=DemandeRepository(),
            proposition_repository=PropositionRepository(),
            epreuve_confirmation_repository=EpreuveConfirmationRepository(),
            doctorat_repository=DoctoratRepository(),
        ),
    }
