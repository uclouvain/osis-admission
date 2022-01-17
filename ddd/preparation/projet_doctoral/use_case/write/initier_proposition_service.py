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
from admission.ddd.preparation.projet_doctoral.builder.proposition_builder import PropositionBuilder
from admission.ddd.preparation.projet_doctoral.commands import InitierPropositionCommand
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import PropositionIdentity
from admission.ddd.preparation.projet_doctoral.domain.service.commission_proximite import CommissionProximite
from admission.ddd.preparation.projet_doctoral.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.preparation.projet_doctoral.domain.service.initier_proposition import MaximumPropositionAutorisee
from admission.ddd.preparation.projet_doctoral.repository.i_proposition import IPropositionRepository


def initier_proposition(
        cmd: 'InitierPropositionCommand',
        proposition_repository: 'IPropositionRepository',
        doctorat_translator: 'IDoctoratTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    doctorat = doctorat_translator.get(cmd.sigle_formation, cmd.annee_formation)
    propositions_candidat = proposition_repository.search(matricule_candidat=cmd.matricule_candidat)
    MaximumPropositionAutorisee().verifier(propositions_candidat)
    CommissionProximite().verifier(doctorat, cmd.commission_proximite)

    # WHEN
    proposition = PropositionBuilder().initier_proposition(cmd, doctorat.entity_id, proposition_repository)

    # THEN
    proposition_repository.save(proposition)

    return proposition.entity_id
