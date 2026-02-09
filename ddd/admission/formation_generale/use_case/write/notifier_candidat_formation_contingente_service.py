##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.formation_generale.commands import (
    NotifierCandidatContingenteNonResidentAcceptationCommand,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.validator.validator_by_business_actions import (
    NotifierCandidatNonResidentContingenteValidatorList,
)
from admission.ddd.admission.formation_generale.repository.i_proposition import (
    IPropositionRepository,
)


def notifier_candidat_formation_contingente(
    cmd: 'NotifierCandidatContingenteNonResidentAcceptationCommand',
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    contingente_service: 'IContingente',
    pdf_generation: 'IPDFGeneration',
    notification: 'INotification',
    historique: 'IHistorique',
) -> None:
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(uuid=cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)

    # WHEN
    NotifierCandidatNonResidentContingenteValidatorList(
        proposition=proposition,
    ).validate()

    # THEN
    contingente_service.notifier_admission(
        proposition_id=proposition_id,
        gestionnaire=cmd.gestionnaire,
        proposition_repository=proposition_repository,
        profil_candidat_translator=profil_candidat_translator,
        pdf_generation=pdf_generation,
        notification=notification,
        historique=historique,
    )
