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

_proposition_repository = PropositionInMemoryRepository()
_groupe_supervision_repository = GroupeDeSupervisionInMemoryRepository()
_demande_repository = DemandeInMemoryRepository()
_academic_year_repository = AcademicYearInMemoryRepository()
_profil_candidat_translator = ProfilCandidatInMemoryTranslator()
_promoteur_translator = PromoteurInMemoryTranslator()
_doctorat_translator = DoctoratInMemoryTranslator()
_bourse_translator = BourseInMemoryTranslator()
_historique = HistoriqueInMemory()
_notification = NotificationInMemory()
_titres_acces = TitresAccesInMemory()


COMMAND_HANDLERS = {
    InitierPropositionCommand: lambda msg_bus, cmd: initier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        doctorat_translator=_doctorat_translator,
        bourse_translator=_bourse_translator,
        historique=_historique,
    ),
    CompleterPropositionCommand: lambda msg_bus, cmd: completer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        doctorat_translator=_doctorat_translator,
        historique=_historique,
    ),
    RechercherDoctoratQuery: lambda msg_bus, cmd: rechercher_doctorats(
        cmd,
        doctorat_translator=_doctorat_translator,
        annee_inscription_formation_translator=AnneeInscriptionFormationInMemoryTranslator(),
    ),
    IdentifierPromoteurCommand: lambda msg_bus, cmd: identifier_promoteur(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        promoteur_translator=_promoteur_translator,
        historique=_historique,
    ),
    IdentifierMembreCACommand: lambda msg_bus, cmd: identifier_membre_CA(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        membre_CA_translator=MembreCAInMemoryTranslator(),
        historique=_historique,
    ),
    DemanderSignaturesCommand: lambda msg_bus, cmd: demander_signatures(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        promoteur_translator=_promoteur_translator,
        historique=_historique,
        notification=_notification,
    ),
    VerifierPropositionCommand: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        profil_candidat_translator=_profil_candidat_translator,
        academic_year_repository=_academic_year_repository,
        titres_acces=_titres_acces,
    ),
    VerifierProjetCommand: lambda msg_bus, cmd: verifier_projet(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        promoteur_translator=_promoteur_translator,
    ),
    SupprimerPromoteurCommand: lambda msg_bus, cmd: supprimer_promoteur(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
        notification=_notification,
    ),
    DesignerPromoteurReferenceCommand: lambda msg_bus, cmd: designer_promoteur_reference(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    SupprimerMembreCACommand: lambda msg_bus, cmd: supprimer_membre_CA(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
        notification=_notification,
    ),
    ApprouverPropositionCommand: lambda msg_bus, cmd: approuver_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
        notification=_notification,
    ),
    RefuserPropositionCommand: lambda msg_bus, cmd: refuser_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
        notification=_notification,
    ),
    SoumettrePropositionCommand: lambda msg_bus, cmd: soumettre_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        demande_repository=_demande_repository,
        profil_candidat_translator=_profil_candidat_translator,
        academic_year_repository=_academic_year_repository,
        historique=_historique,
        notification=_notification,
        titres_acces=_titres_acces,
    ),
    DefinirCotutelleCommand: lambda msg_bus, cmd: definir_cotutelle(
        cmd,
        groupe_supervision_repository=_groupe_supervision_repository,
        proposition_repository=_proposition_repository,
        historique=_historique,
    ),
    ListerPropositionsCandidatQuery: lambda msg_bus, cmd: lister_propositions_candidat(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    ListerPropositionsSuperviseesQuery: lambda msg_bus, cmd: lister_propositions_supervisees(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    GetPropositionCommand: lambda msg_bus, cmd: recuperer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    GetGroupeDeSupervisionCommand: lambda msg_bus, cmd: recuperer_groupe_de_supervision(
        cmd,
        groupe_supervision_repository=_groupe_supervision_repository,
        promoteur_translator=_promoteur_translator,
        membre_ca_translator=MembreCAInMemoryTranslator(),
    ),
    GetCotutelleCommand: lambda msg_bus, cmd: recuperer_cotutelle(
        cmd,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
    ),
    ApprouverPropositionParPdfCommand: lambda msg_bus, cmd: approuver_proposition_par_pdf(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
    ),
    CompleterComptabilitePropositionCommand: lambda msg_bus, cmd: completer_comptabilite_proposition(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    ModifierTypeAdmissionCommand: lambda msg_bus, cmd: modifier_type_admission(
        cmd,
        proposition_repository=_proposition_repository,
        bourse_translator=_bourse_translator,
    ),
}
