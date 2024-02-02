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

from osis_comment.models import CommentEntry
from osis_history.models import HistoryEntry

from admission.ddd.admission.domain.model.enums.condition_acces import TypeTitreAccesSelectionnable
from admission.ddd.admission.domain.repository.i_titre_acces_selectionnable import ITitreAccesSelectionnableRepository
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import IUnitesEnseignementTranslator
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition, PropositionIdentity
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
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO

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
    def get_base_fac_decision_context(
        cls,
        proposition_id: PropositionIdentity,
        gestionnaire: PersonneConnueUclDTO,
        proposition_repository: IPropositionRepository,
        unites_enseignement_translator: IUnitesEnseignementTranslator,
    ):
        proposition_dto = proposition_repository.get_dto_for_gestionnaire(
            proposition_id,
            unites_enseignement_translator,
        )

        comment = CommentEntry.objects.filter(
            object_uuid=proposition_dto.uuid,
            tags=['decision_facultaire', 'FAC'],
        ).first()

        sic_to_fac_history_entry = (
            HistoryEntry.objects.filter(
                object_uuid=proposition_dto.uuid,
                tags__contains=['proposition', 'fac-decision', 'send-to-fac'],
            )
            .order_by('-created')
            .first()
        )

        return {
            'proposition': proposition_dto,
            'fac_decision_comment': comment,
            'sic_to_fac_history_entry': sic_to_fac_history_entry,
            'manager': gestionnaire,
        }

    @classmethod
    def generer_attestation_accord_facultaire(
        cls,
        proposition: Proposition,
        gestionnaire: PersonneConnueUclDTO,
        proposition_repository: IPropositionRepository,
        unites_enseignement_translator: IUnitesEnseignementTranslator,
        profil_candidat_translator: IProfilCandidatTranslator,
        titre_acces_selectionnable_repository: ITitreAccesSelectionnableRepository,
        annee_courante: int,
    ) -> None:
        # Get the information to display on the pdf
        context = cls.get_base_fac_decision_context(
            proposition_id=proposition.entity_id,
            gestionnaire=gestionnaire,
            proposition_repository=proposition_repository,
            unites_enseignement_translator=unites_enseignement_translator,
        )

        # Get the names of the access titles
        access_titles = titre_acces_selectionnable_repository.search_by_proposition(
            proposition_identity=proposition.entity_id,
            seulement_selectionnes=True,
        )

        secondary_studies_dto = None
        cv_dto = None

        context['access_titles_names'] = []

        for access_title in sorted(access_titles, key=lambda title: title.annee, reverse=True):

            # Secondary studies
            if access_title.entity_id.type_titre == TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES:
                if secondary_studies_dto is None:
                    secondary_studies_dto = profil_candidat_translator.get_etudes_secondaires(
                        matricule=proposition.matricule_candidat,
                    )
                context['access_titles_names'].append(secondary_studies_dto.titre_formate)

            # Curriculum experiences
            else:
                if cv_dto is None:
                    cv_dto = profil_candidat_translator.get_curriculum(
                        matricule=proposition.matricule_candidat,
                        annee_courante=annee_courante,
                        uuid_proposition=proposition.entity_id.uuid,
                    )

                context['access_titles_names'].append(
                    next(
                        experience.titre_formate
                        for experience in {
                            TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE: cv_dto.experiences_non_academiques,
                            TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE: cv_dto.experiences_academiques,
                        }[access_title.entity_id.type_titre]
                        if experience.uuid == access_title.entity_id.uuid_experience
                    )
                )

        # Generate the pdf
        token = admission_generate_pdf(
            admission=None,
            template='admission/exports/fac_approval_certificate.html',
            filename='fac_approval_certificate.pdf',
            context=context,
            stylesheets=WeasyprintStylesheets.get_stylesheets(),
            author=gestionnaire.matricule,
        )

        # Store the token of the pdf
        proposition.certificat_approbation_fac = [token]

    @classmethod
    def generer_attestation_refus_facultaire(
        cls,
        proposition: Proposition,
        gestionnaire: PersonneConnueUclDTO,
        proposition_repository: IPropositionRepository,
        unites_enseignement_translator: IUnitesEnseignementTranslator,
    ) -> None:
        # Get the information to display on the pdf
        context = cls.get_base_fac_decision_context(
            proposition_id=proposition.entity_id,
            gestionnaire=gestionnaire,
            proposition_repository=proposition_repository,
            unites_enseignement_translator=unites_enseignement_translator,
        )

        # Generate the pdf
        token = admission_generate_pdf(
            admission=None,
            template='admission/exports/fac_refusal_certificate.html',
            filename='fac_refusal_certificate.pdf',
            context=context,
            stylesheets=WeasyprintStylesheets.get_stylesheets(),
            author=gestionnaire.matricule,
        )

        # Store the token of the pdf
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
