# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext

from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_pdf_generation import IPDFGeneration
from admission.exports.utils import admission_generate_pdf
from admission.infrastructure.admission.formation_generale.repository.proposition import PropositionRepository
from admission.utils import WeasyprintStylesheets


class PDFGeneration(IPDFGeneration):
    @classmethod
    def generer_attestation_accord_facultaire(cls, proposition: Proposition, gestionnaire: str) -> None:
        proposition_dto = PropositionRepository.get_dto(proposition.entity_id)
        token = admission_generate_pdf(
            admission=None,
            template='admission/exports/fac_approval_certificate.html',
            filename='fac_approval_certificate.pdf',
            context={
                'proposition': proposition_dto,
                'content_title': gettext('Faculty approval certificate'),
            },
            stylesheets=WeasyprintStylesheets.get_stylesheets(),
            author=gestionnaire,
        )
        proposition.certificat_approbation_fac = [token]

    @classmethod
    def generer_attestation_refus_facultaire(cls, proposition: Proposition, gestionnaire: str) -> None:
        proposition_dto = PropositionRepository.get_dto(proposition.entity_id)
        token = admission_generate_pdf(
            admission=None,
            template='admission/exports/fac_refusal_certificate.html',
            filename='fac_refusal_certificate.pdf',
            context={
                'proposition': proposition_dto,
                'content_title': gettext('Refusal certificate of faculty'),
            },
            stylesheets=WeasyprintStylesheets.get_stylesheets(),
            author=gestionnaire,
        )
        proposition.certificat_refus_fac = [token]
