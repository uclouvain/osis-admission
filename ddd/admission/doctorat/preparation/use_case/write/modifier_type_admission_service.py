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
from admission.ddd.admission.domain.service.i_bourse import IBourseTranslator
from admission.ddd.admission.doctorat.preparation.commands import ModifierTypeAdmissionCommand
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository


def modifier_type_admission(
    cmd: 'ModifierTypeAdmissionCommand',
    proposition_repository: 'IPropositionRepository',
    bourse_translator: 'IBourseTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    proposition = proposition_repository.get(PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition))
    bourse_erasmus_mundus = bourse_translator.get(cmd.bourse_erasmus_mundus) if cmd.bourse_erasmus_mundus else None

    # WHEN
    proposition.modifier_type_admission(
        bourse_erasmus_mundus=bourse_erasmus_mundus,
        type_admission=cmd.type_admission,
        justification=cmd.justification,
        reponses_questions_specifiques=cmd.reponses_questions_specifiques,
    )

    # THEN
    proposition_repository.save(proposition)

    return proposition.entity_id
