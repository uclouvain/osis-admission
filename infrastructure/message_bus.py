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
from admission.ddd.preparation.projet_doctoral.use_case.read.get_cotutelle import get_cotutelle
from admission.ddd.preparation.projet_doctoral.use_case.read.get_groupe_de_supervision_service import \
    get_groupe_de_supervision
from admission.ddd.preparation.projet_doctoral.use_case.read.get_proposition_service import get_proposition
from admission.ddd.preparation.projet_doctoral.use_case.read.rechercher_doctorats_service import \
    rechercher_doctorats
from admission.ddd.preparation.projet_doctoral.use_case.read.rechercher_propositions_service import \
    rechercher_propositions
from admission.ddd.preparation.projet_doctoral.use_case.write.approuver_proposition_service import \
    approuver_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.completer_proposition_service import \
    completer_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.definir_cotutelle_service import definir_cotutelle
from admission.ddd.preparation.projet_doctoral.use_case.write.demander_signature_service import demander_signature
from admission.ddd.preparation.projet_doctoral.use_case.write.identifier_membre_CA_service import identifier_membre_CA
from admission.ddd.preparation.projet_doctoral.use_case.write.identifier_promoteur_service import \
    identifier_promoteur
from admission.ddd.preparation.projet_doctoral.use_case.write.initier_proposition_service import \
    initier_proposition
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_membre_CA_service import \
    supprimer_membre_CA
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_promoteur_service import \
    supprimer_promoteur
from admission.ddd.preparation.projet_doctoral.use_case.write.supprimer_proposition_service import supprimer_proposition
from admission.infrastructure.preparation.projet_doctoral.domain.service.constitution_supervision import \
    ConstitutionSupervisionService
from admission.infrastructure.preparation.projet_doctoral.domain.service.doctorat import DoctoratTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.membre_CA import MembreCATranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.promoteur import PromoteurTranslator
from admission.infrastructure.preparation.projet_doctoral.domain.service.secteur_ucl import SecteurUclTranslator
from admission.infrastructure.preparation.projet_doctoral.repository.groupe_de_supervision import \
    GroupeDeSupervisionRepository
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
        SearchPropositionsCommand: partial(
            rechercher_propositions,
            proposition_repository=PropositionRepository(),
            doctorat_translator=DoctoratTranslator(),
            secteur_ucl_translator=SecteurUclTranslator(),
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
        DemanderSignatureCommand: partial(
            demander_signature,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            constitution_supervision_these=ConstitutionSupervisionService(),
        ),
        ApprouverPropositionCommand: partial(
            approuver_proposition,
            proposition_repository=PropositionRepository(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
        ),
        SearchDoctoratCommand: partial(
            rechercher_doctorats,
            doctorat_translator=DoctoratTranslator(),
        ),
        SupprimerPropositionCommand: lambda cmd: supprimer_proposition(
            cmd,
            proposition_repository=PropositionRepository(),
        ),
    }
