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

from admission.ddd.preparation.projet_doctoral.commands import (
    ApprouverPropositionCommand,
    DemanderSignatureCommand,
    SearchDoctoratCommand,
    CompleterPropositionCommand,
    InitierPropositionCommand,
    IdentifierPromoteurCommand,
    IdentifierMembreCACommand,
    SupprimerMembreCACommand,
    SupprimerPromoteurCommand,
    SearchPropositionsCommand,
)
from admission.ddd.preparation.projet_doctoral.use_case.read.rechercher_doctorats_service import \
    rechercher_doctorats
from admission.ddd.preparation.projet_doctoral.use_case.read.rechercher_propositions_service import \
    rechercher_propositions
from admission.ddd.preparation.projet_doctoral.use_case.write.approuver_proposition_service import \
    approuver_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.completer_proposition_service import \
    completer_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.demander_signature_service import demander_signature
from admission.ddd.preparation.projet_doctoral.use_case.write.identifier_membre_CA_service import \
    identifier_membre_CA
from admission.ddd.preparation.projet_doctoral.use_case.write.identifier_promoteur_service import \
    identifier_promoteur
from admission.ddd.preparation.projet_doctoral.use_case.write.initier_proposition_service import \
    initier_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_membre_CA_service import \
    supprimer_membre_CA
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_promoteur_service import \
    supprimer_promoteur
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.constitution_supervision import \
    ConstitutionSupervisionInMemoryService
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.doctorat import \
    DoctoratInMemoryTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.membre_CA import \
    MembreCAInMemoryTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.promoteur import \
    PromoteurInMemoryTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.secteur_ucl import \
    SecteurUclInMemoryTranslator
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.groupe_de_supervision import \
    GroupeDeSupervisionInMemoryRepository
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.proposition import \
    PropositionInMemoryRepository
from infrastructure.utils import AbstractMessageBusCommands, MessageBus, load_message_bus_instance


class MessageBusInMemoryCommands(AbstractMessageBusCommands):
    command_handlers = {
        InitierPropositionCommand: lambda cmd: initier_proposition(
            cmd,
            PropositionInMemoryRepository(),
            DoctoratInMemoryTranslator(),
        ),
        SearchDoctoratCommand: lambda cmd: rechercher_doctorats(
            cmd,
            DoctoratInMemoryTranslator(),
        ),
        CompleterPropositionCommand: lambda cmd: completer_proposition(
            cmd,
            PropositionInMemoryRepository(),
            DoctoratInMemoryTranslator(),
        ),
        IdentifierPromoteurCommand: lambda cmd: identifier_promoteur(
            cmd,
            PropositionInMemoryRepository(),
            GroupeDeSupervisionInMemoryRepository(),
            PromoteurInMemoryTranslator(),
        ),
        IdentifierMembreCACommand: lambda cmd: identifier_membre_CA(
            cmd,
            PropositionInMemoryRepository(),
            GroupeDeSupervisionInMemoryRepository(),
            MembreCAInMemoryTranslator(),
        ),
        SupprimerPromoteurCommand: lambda cmd: supprimer_promoteur(
            cmd,
            PropositionInMemoryRepository(),
            GroupeDeSupervisionInMemoryRepository(),
        ),
        SupprimerMembreCACommand: lambda cmd: supprimer_membre_CA(
            cmd,
            PropositionInMemoryRepository(),
            GroupeDeSupervisionInMemoryRepository(),
        ),
        DemanderSignatureCommand: lambda cmd: demander_signature(
            cmd,
            PropositionInMemoryRepository(),
            GroupeDeSupervisionInMemoryRepository(),
            ConstitutionSupervisionInMemoryService(),
        ),
        ApprouverPropositionCommand: lambda cmd: approuver_proposition(
            cmd,
            PropositionInMemoryRepository(),
            GroupeDeSupervisionInMemoryRepository(),
        ),
        SearchPropositionsCommand: lambda cmd: rechercher_propositions(
            cmd,
            PropositionInMemoryRepository(),
            DoctoratInMemoryTranslator(),
            SecteurUclInMemoryTranslator(),
        ),
    }


message_bus_in_memory_instance = MessageBus(MessageBusInMemoryCommands.get_command_handlers())
