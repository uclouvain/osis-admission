##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.doctorat.preparation.commands import *
from admission.ddd.admission.doctorat.preparation.use_case.read import *
from admission.ddd.admission.doctorat.preparation.use_case.write import *
from admission.infrastructure.admission.domain.service.in_memory.annee_inscription_formation import (
    AnneeInscriptionFormationInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from .domain.service.in_memory.doctorat import DoctoratInMemoryTranslator
from .domain.service.in_memory.historique import HistoriqueInMemory
from .domain.service.in_memory.membre_CA import MembreCAInMemoryTranslator
from .domain.service.in_memory.notification import NotificationInMemory
from .domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from .domain.service.in_memory.promoteur import PromoteurInMemoryTranslator
from .repository.in_memory.groupe_de_supervision import GroupeDeSupervisionInMemoryRepository
from .repository.in_memory.proposition import PropositionInMemoryRepository
from ..validation.repository.in_memory.demande import DemandeInMemoryRepository
from ...domain.service.in_memory.titres_acces import TitresAccesInMemory

COMMAND_HANDLERS = {
    InitierPropositionCommand: lambda msg_bus, cmd: initier_proposition(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        doctorat_translator=DoctoratInMemoryTranslator(),
        bourse_translator=BourseInMemoryTranslator(),
        historique=HistoriqueInMemory(),
    ),
    CompleterPropositionCommand: lambda msg_bus, cmd: completer_proposition(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        doctorat_translator=DoctoratInMemoryTranslator(),
        historique=HistoriqueInMemory(),
    ),
    RechercherDoctoratQuery: lambda msg_bus, cmd: rechercher_doctorats(
        cmd,
        doctorat_translator=DoctoratInMemoryTranslator(),
        annee_inscription_formation_translator=AnneeInscriptionFormationInMemoryTranslator(),
    ),
    IdentifierPromoteurCommand: lambda msg_bus, cmd: identifier_promoteur(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        promoteur_translator=PromoteurInMemoryTranslator(),
        historique=HistoriqueInMemory(),
    ),
    IdentifierMembreCACommand: lambda msg_bus, cmd: identifier_membre_CA(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        membre_CA_translator=MembreCAInMemoryTranslator(),
        historique=HistoriqueInMemory(),
    ),
    DemanderSignaturesCommand: lambda msg_bus, cmd: demander_signatures(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        promoteur_translator=PromoteurInMemoryTranslator(),
        historique=HistoriqueInMemory(),
        notification=NotificationInMemory(),
    ),
    VerifierPropositionCommand: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        profil_candidat_translator=ProfilCandidatInMemoryTranslator(),
        academic_year_repository=AcademicYearInMemoryRepository(),
        titres_acces=TitresAccesInMemory(),
    ),
    VerifierProjetCommand: lambda msg_bus, cmd: verifier_projet(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        promoteur_translator=PromoteurInMemoryTranslator(),
    ),
    SupprimerPromoteurCommand: lambda msg_bus, cmd: supprimer_promoteur(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        historique=HistoriqueInMemory(),
        notification=NotificationInMemory(),
    ),
    DesignerPromoteurReferenceCommand: lambda msg_bus, cmd: designer_promoteur_reference(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
    ),
    SupprimerMembreCACommand: lambda msg_bus, cmd: supprimer_membre_CA(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        historique=HistoriqueInMemory(),
        notification=NotificationInMemory(),
    ),
    ApprouverPropositionCommand: lambda msg_bus, cmd: approuver_proposition(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        historique=HistoriqueInMemory(),
        notification=NotificationInMemory(),
    ),
    RefuserPropositionCommand: lambda msg_bus, cmd: refuser_proposition(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        historique=HistoriqueInMemory(),
        notification=NotificationInMemory(),
    ),
    SoumettrePropositionCommand: lambda msg_bus, cmd: soumettre_proposition(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        demande_repository=DemandeInMemoryRepository(),
        profil_candidat_translator=ProfilCandidatInMemoryTranslator(),
        academic_year_repository=AcademicYearInMemoryRepository(),
        historique=HistoriqueInMemory(),
        notification=NotificationInMemory(),
        titres_acces=TitresAccesInMemory(),
    ),
    DefinirCotutelleCommand: lambda msg_bus, cmd: definir_cotutelle(
        cmd,
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        proposition_repository=PropositionInMemoryRepository(),
        historique=HistoriqueInMemory(),
    ),
    ListerPropositionsCandidatQuery: lambda msg_bus, cmd: lister_propositions_candidat(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
    ),
    ListerPropositionsSuperviseesQuery: lambda msg_bus, cmd: lister_propositions_supervisees(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
    ),
    GetPropositionCommand: lambda msg_bus, cmd: recuperer_proposition(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
    ),
    GetGroupeDeSupervisionCommand: lambda msg_bus, cmd: recuperer_groupe_de_supervision(
        cmd,
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        promoteur_translator=PromoteurInMemoryTranslator(),
        membre_ca_translator=MembreCAInMemoryTranslator(),
    ),
    GetCotutelleCommand: lambda msg_bus, cmd: recuperer_cotutelle(
        cmd,
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
    ),
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        historique=HistoriqueInMemory(),
    ),
    ApprouverPropositionParPdfCommand: lambda msg_bus, cmd: approuver_proposition_par_pdf(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        historique=HistoriqueInMemory(),
    ),
    CompleterComptabilitePropositionCommand: lambda msg_bus, cmd: completer_comptabilite_proposition(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
    ),
    ModifierTypeAdmissionCommand: lambda msg_bus, cmd: modifier_type_admission(
        cmd,
        proposition_repository=PropositionInMemoryRepository(),
        bourse_translator=BourseInMemoryTranslator(),
    ),
}
