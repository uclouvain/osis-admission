# ##############################################################################
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
# ##############################################################################
from typing import List, Optional

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.doctorate import ConfirmationPaper
from admission.ddd.projet_doctoral.doctorat.domain.model.doctorat import DoctoratIdentity
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.builder.epreuve_confirmation_identity import \
    EpreuveConfirmationIdentityIdentityBuilder
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.domain.model._demande_prolongation import (
    DemandeProlongation,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmationIdentity,
    EpreuveConfirmation,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.dtos import (
    EpreuveConfirmationDTO,
    DemandeProlongationDTO,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)


class EpreuveConfirmationRepository(IEpreuveConfirmationRepository):
    @classmethod
    def get_dto(cls, entity_id: 'EpreuveConfirmationIdentity') -> 'EpreuveConfirmationDTO':
        try:
            confirmation_paper = ConfirmationPaper.objects.get(uuid=entity_id.uuid)
        except ConfirmationPaper.DoesNotExist:
            raise EpreuveConfirmationNonTrouveeException

        return cls._load_confirmation_dto(confirmation_paper)

    @classmethod
    def search_by_doctorat_identity(cls, doctorat_entity_id: 'DoctoratIdentity') -> List['EpreuveConfirmation']:
        confirmation_papers = ConfirmationPaper.objects.filter(admission__uuid=doctorat_entity_id.uuid)
        return [
            cls._load_confirmation(doctorat_entity_id, confirmation_paper) for confirmation_paper in confirmation_papers
        ]

    @classmethod
    def search_dto_by_doctorat_identity(cls, doctorat_entity_id: 'DoctoratIdentity') -> List['EpreuveConfirmationDTO']:
        confirmation_papers = ConfirmationPaper.objects.filter(admission__uuid=doctorat_entity_id.uuid)
        return [cls._load_confirmation_dto(confirmation_paper) for confirmation_paper in confirmation_papers]

    @classmethod
    def save(cls, entity: 'EpreuveConfirmation') -> 'EpreuveConfirmationIdentity':
        related_admission = DoctorateAdmission.objects.get(uuid=entity.doctorat_id.uuid)

        extended_deadline_params = (
            {
                'extended_deadline': entity.demande_prolongation.nouvelle_echeance,
                'cdd_opinion': entity.demande_prolongation.avis_cdd,
                'justification_letter': entity.demande_prolongation.lettre_justification,
                'brief_justification': entity.demande_prolongation.justification_succincte,
            }
            if entity.demande_prolongation
            else {}
        )

        ConfirmationPaper.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'admission': related_admission,
                'confirmation_date': entity.date,
                'confirmation_deadline': entity.date_limite,
                'research_report': entity.rapport_recherche,
                'supervisor_panel_report': entity.proces_verbal_ca,
                'thesis_funding_renewal': entity.demande_renouvellement_bourse,
                'research_mandate_renewal_opinion': entity.avis_renouvellement_mandat_recherche,
                'certificate_of_failure': entity.attestation_echec,
                'certificate_of_achievement': entity.attestation_reussite,
                **extended_deadline_params,
            },
        )

        return entity.entity_id

    @classmethod
    def get(cls, entity_id: 'EpreuveConfirmationIdentity') -> 'EpreuveConfirmation':
        raise NotImplementedError

    @classmethod
    def search(
        cls, entity_ids: Optional[List['EpreuveConfirmationIdentity']] = None, **kwargs
    ) -> List[EpreuveConfirmation]:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'EpreuveConfirmationIdentity', **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def _load_confirmation_dto(cls, confirmation_paper: ConfirmationPaper) -> EpreuveConfirmationDTO:
        return EpreuveConfirmationDTO(
            uuid=str(confirmation_paper.uuid),
            date_limite=confirmation_paper.confirmation_deadline,
            date=confirmation_paper.confirmation_date,
            rapport_recherche=confirmation_paper.research_report,
            demande_prolongation=DemandeProlongationDTO(
                nouvelle_echeance=confirmation_paper.extended_deadline,
                justification_succincte=confirmation_paper.brief_justification,
                lettre_justification=confirmation_paper.justification_letter,
                avis_cdd=confirmation_paper.cdd_opinion,
            )
            if confirmation_paper.extended_deadline
            else None,
            proces_verbal_ca=confirmation_paper.supervisor_panel_report,
            attestation_reussite=confirmation_paper.certificate_of_achievement,
            attestation_echec=confirmation_paper.certificate_of_failure,
            demande_renouvellement_bourse=confirmation_paper.thesis_funding_renewal,
            avis_renouvellement_mandat_recherche=confirmation_paper.research_mandate_renewal_opinion,
        )

    @classmethod
    def _load_confirmation(
        cls,
        entity_id: 'DoctoratIdentity',
        confirmation_paper: ConfirmationPaper,
    ) -> EpreuveConfirmation:
        return EpreuveConfirmation(
            entity_id=EpreuveConfirmationIdentityIdentityBuilder.build_from_uuid(str(confirmation_paper.uuid)),
            doctorat_id=entity_id,
            date_limite=confirmation_paper.confirmation_deadline,
            date=confirmation_paper.confirmation_date,
            rapport_recherche=confirmation_paper.research_report,
            demande_prolongation=DemandeProlongation(
                nouvelle_echeance=confirmation_paper.extended_deadline,
                justification_succincte=confirmation_paper.brief_justification,
                lettre_justification=confirmation_paper.justification_letter,
                avis_cdd=confirmation_paper.cdd_opinion,
            )
            if confirmation_paper.extended_deadline
            else None,
            proces_verbal_ca=confirmation_paper.supervisor_panel_report,
            attestation_reussite=confirmation_paper.certificate_of_achievement,
            attestation_echec=confirmation_paper.certificate_of_failure,
            demande_renouvellement_bourse=confirmation_paper.thesis_funding_renewal,
            avis_renouvellement_mandat_recherche=confirmation_paper.research_mandate_renewal_opinion,
        )
