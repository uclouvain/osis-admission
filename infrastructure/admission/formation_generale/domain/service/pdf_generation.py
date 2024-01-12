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
from typing import Optional

from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext
from osis_document.utils import confirm_upload

from admission.ddd.admission.enums.emplacement_document import (
    StatutEmplacementDocument,
    EMPLACEMENTS_DOCUMENTS_RECLAMABLES,
)
from admission.ddd.admission.formation_generale.commands import RecupererDocumentsPropositionQuery
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_pdf_generation import IPDFGeneration
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PdfSicInconnu
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.exports.utils import admission_generate_pdf
from admission.infrastructure.admission.domain.service.unites_enseignement_translator import (
    UnitesEnseignementTranslator,
)
from admission.utils import WeasyprintStylesheets
from base.models.enums.mandate_type import MandateTypes
from base.models.person import Person

ENTITY_SIC = 'SIC'


class PDFGeneration(IPDFGeneration):
    @classmethod
    def _get_sic_director(cls):
        director = Person.objects.filter(
            mandatary__mandate__entity__entityversion__acronym=ENTITY_SIC,
            mandatary__mandate__function=MandateTypes.DIRECTOR.name,
        ).first()
        return director

    @classmethod
    def generer_attestation_accord_facultaire(
        cls,
        proposition_repository: IPropositionRepository,
        proposition: Proposition,
        gestionnaire: str,
    ) -> None:
        proposition_dto = proposition_repository.get_dto(proposition.entity_id)
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
    def generer_attestation_refus_facultaire(
        cls,
        proposition_repository: IPropositionRepository,
        proposition: Proposition,
        gestionnaire: str,
    ) -> None:
        proposition_dto = proposition_repository.get_dto(proposition.entity_id)
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

    @classmethod
    def generer_sic_temporaire(
        cls,
        proposition_repository: IPropositionRepository,
        proposition: Proposition,
        gestionnaire: str,
        pdf: str,
    ) -> Optional[str]:
        PDF_GENERATION_METHOD = {
            'accord': cls.generer_attestation_accord_sic,
            'accord_annexe': cls.generer_attestation_accord_annexe_sic,
            'refus': cls.generer_attestation_refus_sic,
        }

        pdf_generation_method = PDF_GENERATION_METHOD.get(pdf)
        if pdf_generation_method is None:
            raise PdfSicInconnu()
        return pdf_generation_method(
            proposition_repository=proposition_repository,
            proposition=proposition,
            gestionnaire=gestionnaire,
            temporaire=True,
        )

    @classmethod
    def generer_attestation_accord_sic(
        cls,
        proposition_repository: IPropositionRepository,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        from infrastructure.messages_bus import message_bus_instance

        proposition_dto = proposition_repository.get_dto_for_gestionnaire(
            proposition.entity_id, UnitesEnseignementTranslator
        )
        documents = [
            document
            for document in message_bus_instance.invoke(
                RecupererDocumentsPropositionQuery(
                    uuid_proposition=proposition_dto.uuid,
                )
            )
            if document.statut == StatutEmplacementDocument.A_RECLAMER.name
            and document.type in EMPLACEMENTS_DOCUMENTS_RECLAMABLES
        ]

        token = admission_generate_pdf(
            admission=None,
            template='admission/exports/sic_approval_certificate.html',
            filename=f'Autorisation_inscription_Dossier_{proposition_dto.reference}.pdf',
            context={
                'proposition': proposition_dto,
                'documents': documents,
                'director': cls._get_sic_director(),
            },
            author=gestionnaire,
            language=proposition_dto.langue_contact_candidat,
        )
        if temporaire:
            return token
        proposition.certificat_approbation_sic = [token]

    @classmethod
    def generer_attestation_accord_annexe_sic(
        cls,
        proposition_repository: IPropositionRepository,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        with translation.override(settings.LANGUAGE_CODE_FR):
            proposition_dto = proposition_repository.get_dto_for_gestionnaire(
                proposition.entity_id, UnitesEnseignementTranslator
            )
            token = admission_generate_pdf(
                admission=None,
                template='admission/exports/sic_approval_annexe.html',
                filename='Formulaire_pour_la_demande_de_visa.pdf',
                context={
                    'proposition': proposition_dto,
                    'director': cls._get_sic_director(),
                },
                author=gestionnaire,
            )
        if temporaire:
            return token
        proposition.certificat_approbation_sic_annexe = [token]

    @classmethod
    def generer_attestation_refus_sic(
        cls,
        proposition_repository: IPropositionRepository,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        with translation.override(settings.LANGUAGE_CODE_FR):
            proposition_dto = proposition_repository.get_dto_for_gestionnaire(
                proposition.entity_id, UnitesEnseignementTranslator
            )
            token = admission_generate_pdf(
                admission=None,
                template='admission/exports/sic_refusal_certificate.html',
                filename=f'UCLouvain_{proposition_dto.reference}.pdf',
                context={
                    'proposition': proposition_dto,
                    'director': cls._get_sic_director(),
                },
                author=gestionnaire,
            )
        if temporaire:
            return token
        proposition.certificat_refus_sic = [token]

    @classmethod
    def generer_attestation_refus_inscription_sic(
        cls,
        proposition_repository: IPropositionRepository,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        with translation.override(settings.LANGUAGE_CODE_FR):
            proposition_dto = proposition_repository.get_dto_for_gestionnaire(
                proposition.entity_id, UnitesEnseignementTranslator
            )
            token = admission_generate_pdf(
                admission=None,
                template='admission/exports/sic_inscription_refusal_certificate.html',
                filename=f'UCLouvain_{proposition_dto.reference}.pdf',
                context={
                    'proposition': proposition_dto,
                    'director': cls._get_sic_director(),
                },
                author=gestionnaire,
            )
        if temporaire:
            return token
        proposition.certificat_refus_sic = [token]
