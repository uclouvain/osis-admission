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

from admission.ddd.preparation.projet_doctoral.commands import (
    ApprouverPropositionCommand,
    CompleterPropositionCommand,
    DemanderSignatureCommand, GetPropositionCommand, IdentifierPromoteurCommand,
    InitierPropositionCommand,
    SearchDoctoratCommand,
    SearchPropositionsCommand,
    SupprimerMembreCACommand,
    SupprimerPromoteurCommand,
)
from admission.ddd.preparation.projet_doctoral.use_case.read.get_proposition_service import get_proposition
from admission.ddd.preparation.projet_doctoral.use_case.read.rechercher_doctorats_service import \
    rechercher_doctorats
from admission.ddd.preparation.projet_doctoral.use_case.read.rechercher_propositions_service import \
    rechercher_propositions
from admission.ddd.preparation.projet_doctoral.use_case.write.approuver_proposition_service import \
    approuver_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.completer_proposition_service import \
    completer_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.demander_signature_service import demander_signature
from admission.ddd.preparation.projet_doctoral.use_case.write.identifier_promoteur_service import \
    identifier_promoteur
from admission.ddd.preparation.projet_doctoral.use_case.write.initier_proposition_service import \
    initier_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_membre_CA_service import \
    supprimer_membre_CA
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_promoteur_service import \
    supprimer_promoteur
from admission.infrastructure.preparation.projet_doctoral.domain.service.constitution_supervision import \
    ConstitutionSupervisionService
from admission.infrastructure.preparation.projet_doctoral.domain.service.doctorat import DoctoratTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.promoteur import PromoteurTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.secteur_ucl import SecteurUclTranslator
from admission.infrastructure.preparation.projet_doctoral.repository.groupe_de_supervision import \
    GroupeDeSupervisionRepository
from admission.infrastructure.preparation.projet_doctoral.repository.proposition import PropositionRepository
from infrastructure.utils import AbstractMessageBusCommands


class MessageBusCommands(AbstractMessageBusCommands):
    command_handlers = {
        InitierPropositionCommand: lambda cmd: initier_proposition(
            cmd,
            PropositionRepository(),
            DoctoratTranslator(),
        ),
        SearchPropositionsCommand: lambda cmd: rechercher_propositions(
            cmd,
            PropositionRepository(),
            DoctoratTranslator(),
            SecteurUclTranslator(),
        ),
        GetPropositionCommand: lambda cmd: get_proposition(
            cmd,
            PropositionRepository(),
            DoctoratTranslator(),
            SecteurUclTranslator(),
        ),
        CompleterPropositionCommand: lambda cmd: completer_proposition(
            cmd,
            PropositionRepository(),
            DoctoratTranslator(),
        ),
        IdentifierPromoteurCommand: lambda cmd: identifier_promoteur(
            cmd,
            PropositionRepository(),
            GroupeDeSupervisionRepository(),
            PromoteurTranslator(),
        ),
        SupprimerPromoteurCommand: lambda cmd: supprimer_promoteur(
            cmd,
            PropositionRepository(),
            GroupeDeSupervisionRepository(),
        ),
        SupprimerMembreCACommand: lambda cmd: supprimer_membre_CA(
            cmd,
            PropositionRepository(),
            GroupeDeSupervisionRepository(),
        ),
        DemanderSignatureCommand: lambda cmd: demander_signature(
            cmd,
            PropositionRepository(),
            GroupeDeSupervisionRepository(),
            ConstitutionSupervisionService(),
        ),
        ApprouverPropositionCommand: lambda cmd: approuver_proposition(
            cmd,
            PropositionRepository(),
            GroupeDeSupervisionRepository(),
        ),
        SearchDoctoratCommand: lambda cmd: rechercher_doctorats(
            cmd,
            DoctoratTranslator(),
        ),
    }
