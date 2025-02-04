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
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.doctorat.validation.builder.demande_identity import DemandeIdentityBuilder
from admission.ddd.admission.doctorat.validation.commands import ApprouverDemandeCddCommand
from admission.ddd.admission.doctorat.validation.domain.model.demande import DemandeIdentity
from admission.ddd.admission.doctorat.validation.domain.service.proposition_identity import (
    PropositionIdentityTranslator,
)
from admission.ddd.admission.doctorat.validation.repository.i_demande import IDemandeRepository


def approuver_demande_cdd(
    cmd: 'ApprouverDemandeCddCommand',
    demande_repository: 'IDemandeRepository',
    proposition_repository: 'IPropositionRepository',
) -> 'DemandeIdentity':
    # GIVEN
    demande_id = DemandeIdentityBuilder.build_from_uuid(cmd.uuid)
    demande = demande_repository.get(entity_id=demande_id)

    proposition_id = PropositionIdentityTranslator.convertir_depuis_demande(demande_id)
    proposition = proposition_repository.get(entity_id=proposition_id)

    # WHEN
    demande.approuver_cdd()

    # TODO Both SIC and CDD must approved the proposition
    proposition.valider_inscription()

    # THEN
    demande_repository.save(demande)
    proposition_repository.save(proposition)

    return demande.entity_id
