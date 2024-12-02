# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from admission.ddd.admission.doctorat.preparation.builder.proposition_builder import IPropositionBuilder
from admission.ddd.admission.doctorat.preparation.commands import InitierPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository


class PropositionBuilderInMemory(IPropositionBuilder):
    @classmethod
    def initier_nouvelle_proposition_attachee_a_pre_admission(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
    ) -> PropositionIdentity:
        return cls.initier_nouvelle_proposition_non_attachee_a_pre_admission(
            cmd=cmd,
            doctorat_translator=doctorat_translator,
            proposition_repository=proposition_repository,
        )
