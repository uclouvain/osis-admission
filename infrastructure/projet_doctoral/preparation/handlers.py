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
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from .domain.service.doctorat import DoctoratTranslator
from .domain.service.historique import Historique
from .domain.service.notification import Notification
from .domain.service.membre_CA import MembreCATranslator
from .domain.service.profil_candidat import ProfilCandidatTranslator
from .domain.service.promoteur import PromoteurTranslator
from .repository.groupe_de_supervision import GroupeDeSupervisionRepository
from .repository.proposition import PropositionRepository
from ..validation.repository.demande import DemandeRepository

COMMAND_HANDLERS = {
    InitierPropositionCommand: partial(
        initier_proposition,
        proposition_repository=PropositionRepository(),
        doctorat_translator=DoctoratTranslator(),
        historique=Historique(),
    ),
    CompleterPropositionCommand: partial(
        completer_proposition,
        proposition_repository=PropositionRepository(),
        doctorat_translator=DoctoratTranslator(),
        historique=Historique(),
    ),
    RechercherDoctoratCommand: partial(
        rechercher_doctorats,
        doctorat_translator=DoctoratTranslator(),
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
    DemanderSignaturesCommand: partial(
        demander_signatures,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        historique=Historique(),
        notification=Notification(),
    ),
    VerifierPropositionCommand: partial(
        verifier_proposition,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        academic_year_repository=AcademicYearRepository(),
    ),
    VerifierProjetCommand: partial(
        verifier_projet,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
    ),
    SupprimerPromoteurCommand: partial(
        supprimer_promoteur,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    DesignerPromoteurReferenceCommand: partial(
        designer_promoteur_reference,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
    ),
    SupprimerMembreCACommand: partial(
        supprimer_membre_CA,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
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
    RefuserPropositionCommand: partial(
        refuser_proposition,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
        notification=Notification(),
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
    DefinirCotutelleCommand: partial(
        definir_cotutelle,
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        proposition_repository=PropositionRepository(),
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
    GetGroupeDeSupervisionCommand: partial(
        recuperer_groupe_de_supervision,
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        membre_ca_translator=MembreCATranslator(),
    ),
    GetCotutelleCommand: partial(
        recuperer_cotutelle,
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
    ),
    SupprimerPropositionCommand: partial(
        supprimer_proposition,
        proposition_repository=PropositionRepository(),
        historique=Historique(),
    ),
    ApprouverPropositionParPdfCommand: partial(
        approuver_proposition_par_pdf,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
    ),
    CompleterComptabilitePropositionCommand: partial(
        completer_comptabilite_proposition,
        proposition_repository=PropositionRepository(),
    ),
}
