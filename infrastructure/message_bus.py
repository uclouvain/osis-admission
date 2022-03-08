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
from admission.infrastructure.projet_doctoral.preparation.domain.service.doctorat import DoctoratTranslator
from admission.infrastructure.projet_doctoral.preparation.domain.service.historique import Historique
from admission.infrastructure.projet_doctoral.preparation.domain.service.membre_CA import MembreCATranslator
from admission.infrastructure.projet_doctoral.preparation.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.infrastructure.projet_doctoral.preparation.domain.service.promoteur import PromoteurTranslator
from admission.infrastructure.projet_doctoral.preparation.domain.service.secteur_ucl import SecteurUclTranslator
from admission.infrastructure.projet_doctoral.preparation.repository.groupe_de_supervision import (
    GroupeDeSupervisionRepository,
)
from admission.infrastructure.projet_doctoral.preparation.repository.proposition import PropositionRepository
from admission.infrastructure.projet_doctoral.validation.repository.demande import DemandeRepository
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator
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
            doctorat_translator=DoctoratTranslator(),
            secteur_ucl_translator=SecteurUclTranslator(),
            personne_connue_ucl_translator=PersonneConnueUclTranslator(),
        ),
        GetPropositionCommand: partial(
            recuperer_proposition,
            proposition_repository=PropositionRepository(),
            doctorat_translator=DoctoratTranslator(),
            secteur_ucl_translator=SecteurUclTranslator(),
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
        ),
        SupprimerMembreCACommand: partial(
            supprimer_membre_CA,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            historique=Historique(),
        ),
        DemanderSignaturesCommand: partial(
            demander_signatures,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
            historique=Historique(),
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
        ),
        ApprouverPropositionCommand: partial(
            approuver_proposition,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            historique=Historique(),
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
    }
