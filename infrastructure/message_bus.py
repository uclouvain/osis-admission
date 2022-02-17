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

from admission.ddd.preparation.projet_doctoral.commands import *
from admission.ddd.preparation.projet_doctoral.use_case.read import *
from admission.ddd.preparation.projet_doctoral.use_case.write import *
from admission.infrastructure.preparation.projet_doctoral.domain.service.doctorat import DoctoratTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.membre_CA import MembreCATranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.promoteur import PromoteurTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.secteur_ucl import SecteurUclTranslator
from admission.infrastructure.preparation.projet_doctoral.repository.groupe_de_supervision import (
    GroupeDeSupervisionRepository,
)
from admission.infrastructure.preparation.projet_doctoral.repository.proposition import PropositionRepository
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator
from infrastructure.utils import AbstractMessageBusCommands


class MessageBusCommands(AbstractMessageBusCommands):
    command_handlers = {
        InitierPropositionCommand: partial(
            initier_proposition,
            proposition_repository=PropositionRepository(),
            doctorat_translator=DoctoratTranslator(),
        ),
        SearchPropositionsCandidatCommand: partial(
            rechercher_propositions_candidat,
            proposition_repository=PropositionRepository(),
            doctorat_translator=DoctoratTranslator(),
            secteur_ucl_translator=SecteurUclTranslator(),
            personne_connue_ucl_translator=PersonneConnueUclTranslator(),
        ),
        SearchPropositionsSuperviseesCommand: partial(
            rechercher_propositions_supervisees,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            doctorat_translator=DoctoratTranslator(),
            secteur_ucl_translator=SecteurUclTranslator(),
            personne_connue_ucl_translator=PersonneConnueUclTranslator(),
        ),
        GetPropositionCommand: partial(
            get_proposition,
            proposition_repository=PropositionRepository(),
            doctorat_translator=DoctoratTranslator(),
            secteur_ucl_translator=SecteurUclTranslator(),
        ),
        CompleterPropositionCommand: partial(
            completer_proposition,
            proposition_repository=PropositionRepository(),
            doctorat_translator=DoctoratTranslator(),
        ),
        DefinirCotutelleCommand: partial(
            definir_cotutelle,
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        GetCotutelleCommand: partial(
            get_cotutelle,
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        IdentifierPromoteurCommand: partial(
            identifier_promoteur,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
        ),
        IdentifierMembreCACommand: partial(
            identifier_membre_CA,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            membre_CA_translator=MembreCATranslator(),
        ),
        GetGroupeDeSupervisionCommand: partial(
            get_groupe_de_supervision,
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            personne_connue_ucl_translator=PersonneConnueUclTranslator(),
            promoteur_translator=PromoteurTranslator(),
        ),
        SupprimerPromoteurCommand: partial(
            supprimer_promoteur,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        SupprimerMembreCACommand: partial(
            supprimer_membre_CA,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        DemanderSignaturesCommand: partial(
            demander_signatures,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
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
            profil_candidat_translator=ProfilCandidatTranslator(),
        ),
        ApprouverPropositionCommand: partial(
            approuver_proposition,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        ApprouverPropositionParPdfCommand: partial(
            approuver_proposition_par_pdf,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        RefuserPropositionCommand: partial(
            refuser_proposition,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        SearchDoctoratCommand: partial(
            rechercher_doctorats,
            doctorat_translator=DoctoratTranslator(),
        ),
        SupprimerPropositionCommand: partial(
            supprimer_proposition,
            proposition_repository=PropositionRepository(),
        ),
    }
