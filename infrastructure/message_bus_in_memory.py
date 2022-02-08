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

from admission.ddd.preparation.projet_doctoral.commands import *
from admission.ddd.preparation.projet_doctoral.use_case.read.get_cotutelle_service import get_cotutelle
from admission.ddd.preparation.projet_doctoral.use_case.read.get_groupe_de_supervision_service import \
    get_groupe_de_supervision
from admission.ddd.preparation.projet_doctoral.use_case.read.get_proposition_service import get_proposition
from admission.ddd.preparation.projet_doctoral.use_case.read.rechercher_doctorats_service import \
    rechercher_doctorats
from admission.ddd.preparation.projet_doctoral.use_case.read.rechercher_propositions_candidat_service import \
    rechercher_propositions_candidat
from admission.ddd.preparation.projet_doctoral.use_case.read.rechercher_propositions_membre import \
    rechercher_propositions_membre
from admission.ddd.preparation.projet_doctoral.use_case.read.verifier_projet_service import verifier_projet
from admission.ddd.preparation.projet_doctoral.use_case.read.verifier_proposition_service import verifier_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.approuver_proposition_service import \
    approuver_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.completer_proposition_service import \
    completer_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.definir_cotutelle_service import definir_cotutelle
from admission.ddd.preparation.projet_doctoral.use_case.write.demander_signatures_service import demander_signatures
from admission.ddd.preparation.projet_doctoral.use_case.write.identifier_membre_CA_service import \
    identifier_membre_CA
from admission.ddd.preparation.projet_doctoral.use_case.write.identifier_promoteur_service import \
    identifier_promoteur
from admission.ddd.preparation.projet_doctoral.use_case.write.initier_proposition_service import \
    initier_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.refuser_proposition_service import refuser_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_membre_CA_service import \
    supprimer_membre_CA
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_promoteur_service import \
    supprimer_promoteur
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_proposition_service import supprimer_proposition
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.doctorat import \
    DoctoratInMemoryTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.membre_CA import \
    MembreCAInMemoryTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.profil_candidat import \
    ProfilCandidatInMemoryTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.promoteur import \
    PromoteurInMemoryTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.in_memory.secteur_ucl import \
    SecteurUclInMemoryTranslator
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.groupe_de_supervision import \
    GroupeDeSupervisionInMemoryRepository
from admission.infrastructure.preparation.projet_doctoral.repository.in_memory.proposition import \
    PropositionInMemoryRepository
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import \
    PersonneConnueUclInMemoryTranslator
from infrastructure.utils import AbstractMessageBusCommands, MessageBus


class MessageBusInMemoryCommands(AbstractMessageBusCommands):
    command_handlers = {
        InitierPropositionCommand: partial(
            initier_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            doctorat_translator=DoctoratInMemoryTranslator(),
        ),
        SearchDoctoratCommand: partial(
            rechercher_doctorats,
            doctorat_translator=DoctoratInMemoryTranslator(),
        ),
        CompleterPropositionCommand: partial(
            completer_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            doctorat_translator=DoctoratInMemoryTranslator(),
        ),
        GetPropositionCommand: partial(
            get_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            doctorat_translator=DoctoratInMemoryTranslator(),
            secteur_ucl_translator=SecteurUclInMemoryTranslator(),
        ),
        DefinirCotutelleCommand: partial(
            definir_cotutelle,
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        ),
        GetCotutelleCommand: partial(
            get_cotutelle,
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        ),
        IdentifierPromoteurCommand: partial(
            identifier_promoteur,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            promoteur_translator=PromoteurInMemoryTranslator(),
        ),
        IdentifierMembreCACommand: partial(
            identifier_membre_CA,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            membre_CA_translator=MembreCAInMemoryTranslator(),
        ),
        GetGroupeDeSupervisionCommand: partial(
            get_groupe_de_supervision,
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            personne_connue_ucl_translator=PersonneConnueUclInMemoryTranslator(),
            promoteur_translator=PromoteurInMemoryTranslator(),
        ),
        SupprimerPromoteurCommand: partial(
            supprimer_promoteur,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        ),
        SupprimerMembreCACommand: partial(
            supprimer_membre_CA,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        ),
        DemanderSignaturesCommand: partial(
            demander_signatures,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            promoteur_translator=PromoteurInMemoryTranslator(),
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
        ),
        ApprouverPropositionCommand: partial(
            approuver_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        ),
        RefuserPropositionCommand: partial(
            refuser_proposition,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
        ),
        SearchPropositionsCandidatCommand: partial(
            rechercher_propositions_candidat,
            proposition_repository=PropositionInMemoryRepository(),
            doctorat_translator=DoctoratInMemoryTranslator(),
            secteur_ucl_translator=SecteurUclInMemoryTranslator(),
        ),
        SearchPropositionsComiteCommand: partial(
            rechercher_propositions_membre,
            proposition_repository=PropositionInMemoryRepository(),
            groupe_supervision_repository=GroupeDeSupervisionInMemoryRepository(),
            doctorat_translator=DoctoratInMemoryTranslator(),
            secteur_ucl_translator=SecteurUclInMemoryTranslator(),
        ),
        SupprimerPropositionCommand: partial(
            supprimer_proposition,
            proposition_repository=PropositionInMemoryRepository(),
        ),
    }


message_bus_in_memory_instance = MessageBus(MessageBusInMemoryCommands.get_command_handlers())
