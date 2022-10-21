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
from functools import partial

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

COMMAND_HANDLERS = {
    InitierPropositionCommand: partial(
        initier_proposition,
        proposition_repository=PropositionInMemoryRepository(),
        doctorat_translator=DoctoratInMemoryTranslator(),
        bourse_translator=BourseInMemoryTranslator(),
        historique=HistoriqueInMemory(),
    ),
    CompleterPropositionCommand: partial(
        completer_proposition,
        proposition_repository=PropositionInMemoryRepository(),
        doctorat_translator=DoctoratInMemoryTranslator(),
        historique=HistoriqueInMemory(),
    ),
    RechercherDoctoratQuery: partial(
        rechercher_doctorats,
        doctorat_translator=DoctoratInMemoryTranslator(),
        annee_inscription_formation_translator=AnneeInscriptionFormationInMemoryTranslator(),
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
    DemanderSignaturesCommand: partial(
        demander_signatures,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        promoteur_translator=PromoteurInMemoryTranslator(),
        historique=HistoriqueInMemory(),
        notification=NotificationInMemory(),
    ),
    VerifierPropositionCommand: partial(
        verifier_proposition,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        profil_candidat_translator=ProfilCandidatInMemoryTranslator(),
        academic_year_repository=AcademicYearInMemoryRepository(),
    ),
    VerifierProjetCommand: partial(
        verifier_projet,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        promoteur_translator=PromoteurInMemoryTranslator(),
    ),
    SupprimerPromoteurCommand: partial(
        supprimer_promoteur,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        historique=HistoriqueInMemory(),
        notification=NotificationInMemory(),
    ),
    DesignerPromoteurReferenceCommand: partial(
        designer_promoteur_reference,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
    ),
    SupprimerMembreCACommand: partial(
        supprimer_membre_CA,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
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
    RefuserPropositionCommand: partial(
        refuser_proposition,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        historique=HistoriqueInMemory(),
        notification=NotificationInMemory(),
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
    DefinirCotutelleCommand: partial(
        definir_cotutelle,
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        proposition_repository=PropositionInMemoryRepository(),
        historique=HistoriqueInMemory(),
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
    GetPropositionCommand: partial(
        recuperer_proposition,
        proposition_repository=PropositionInMemoryRepository(),
    ),
    GetGroupeDeSupervisionCommand: partial(
        recuperer_groupe_de_supervision,
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        promoteur_translator=PromoteurInMemoryTranslator(),
        membre_ca_translator=MembreCAInMemoryTranslator(),
    ),
    GetCotutelleCommand: partial(
        recuperer_cotutelle,
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
    ),
    SupprimerPropositionCommand: partial(
        supprimer_proposition,
        proposition_repository=PropositionInMemoryRepository(),
        historique=HistoriqueInMemory(),
    ),
    ApprouverPropositionParPdfCommand: partial(
        approuver_proposition_par_pdf,
        proposition_repository=PropositionInMemoryRepository(),
        groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        historique=HistoriqueInMemory(),
    ),
    CompleterComptabilitePropositionCommand: partial(
        completer_comptabilite_proposition,
        proposition_repository=PropositionInMemoryRepository(),
    ),
    ModifierTypeAdmissionCommand: partial(
        modifier_type_admission,
        proposition_repository=PropositionInMemoryRepository(),
        bourse_translator=BourseInMemoryTranslator(),
    ),
}
