# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import itertools
from typing import Dict, List, Optional, Union

from django.conf import settings
from django.utils import timezone, translation
from django.utils.translation import override
from osis_comment.models import CommentEntry
from osis_history.models import HistoryEntry

from admission.constants import ORDERED_CAMPUSES_UUIDS
from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererResumeEtEmplacementsDocumentsPropositionQuery,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist,
    TypeDeRefus,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_pdf_generation import (
    IPDFGeneration,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    PdfSicInconnu,
)
from admission.ddd.admission.doctorat.preparation.dtos import GroupeDeSupervisionDTO
from admission.ddd.admission.doctorat.preparation.dtos.proposition import (
    PropositionGestionnaireDTO,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import (
    IPropositionRepository,
)
from admission.ddd.admission.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnable,
)
from admission.ddd.admission.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.domain.service.i_unites_enseignement_translator import (
    IUnitesEnseignementTranslator,
)
from admission.ddd.admission.dtos.resume import (
    ResumeEtEmplacementsDocumentsPropositionDTO,
)
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.exports.utils import admission_generate_pdf
from admission.infrastructure.admission.domain.service.unites_enseignement_translator import (
    UnitesEnseignementTranslator,
)
from admission.infrastructure.utils import CHAMPS_DOCUMENTS_EXPERIENCES_CURRICULUM
from admission.utils import WeasyprintStylesheets
from base.models.enums.mandate_type import MandateTypes
from base.models.person import Person
from ddd.logic.formation_catalogue.commands import GetCreditsDeLaFormationQuery
from ddd.logic.shared_kernel.campus.domain.model.uclouvain_campus import (
    UclouvainCampusIdentity,
)
from ddd.logic.shared_kernel.campus.repository.i_uclouvain_campus import (
    IUclouvainCampusRepository,
)
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import (
    IExperienceParcoursInterneTranslator,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    ExperienceAcademiqueDTO,
    ExperienceNonAcademiqueDTO,
)
from reference.services.mandates import (
    MandateFunctionEnum,
    MandatesException,
    MandatesService,
)

ENTITY_SIC = 'SIC'
ENTITY_SICB = 'SICB'
ENTITY_UCL = 'UCL'


class PDFGeneration(IPDFGeneration):
    @classmethod
    def _get_refusal_certificate_footer_campus(
        cls,
        proposition_dto: PropositionGestionnaireDTO,
        campus_repository: IUclouvainCampusRepository,
    ):
        footer_campus_uuid = (
            # For the trainings whose the enrollment is in Saint-Louis, the campus to display is the related one
            ORDERED_CAMPUSES_UUIDS['BRUXELLES_SAINT_LOUIS_UUID']
            if proposition_dto.formation.campus_inscription
            and proposition_dto.formation.campus_inscription.uuid
            == ORDERED_CAMPUSES_UUIDS['BRUXELLES_SAINT_LOUIS_UUID']
            # For other trainings, the campus to display is the Louvain-La-Neuve campus (default)
            else ORDERED_CAMPUSES_UUIDS['LOUVAIN_LA_NEUVE_UUID']
        )
        return campus_repository.get_dto(UclouvainCampusIdentity(uuid=str(footer_campus_uuid)))

    @classmethod
    def _get_sic_director(cls, proposition_dto: PropositionGestionnaireDTO):
        now = timezone.now()

        # For the trainings whose the enrollment is in Saint-Louis, the director is the Saint-Louis campus sic director
        entity = (
            ENTITY_SICB
            if proposition_dto.formation.campus_inscription
            and proposition_dto.formation.campus_inscription.uuid
            == ORDERED_CAMPUSES_UUIDS['BRUXELLES_SAINT_LOUIS_UUID']
            else ENTITY_SIC
        )

        director = (
            Person.objects.filter(
                mandatary__mandate__entity__entityversion__acronym=entity,
                mandatary__mandate__function=MandateTypes.DIRECTOR.name,
            )
            .filter(
                mandatary__start_date__lte=now,
                mandatary__end_date__gte=now,
            )
            .first()
        )
        return director

    @classmethod
    def _get_sic_rector(cls):
        now = timezone.now()
        rector = (
            Person.objects.filter(
                mandatary__mandate__entity__entityversion__acronym=ENTITY_UCL,
                mandatary__mandate__function=MandateTypes.RECTOR.name,
            )
            .filter(
                mandatary__start_date__lte=now,
                mandatary__end_date__gte=now,
            )
            .first()
        )
        return rector

    @classmethod
    def get_base_fac_decision_context(
        cls,
        proposition_id: PropositionIdentity,
        proposition_repository: IPropositionRepository,
        unites_enseignement_translator: IUnitesEnseignementTranslator,
        groupe_supervision_dto: GroupeDeSupervisionDTO,
    ):
        proposition_dto = proposition_repository.get_dto_for_gestionnaire(
            proposition_id,
            unites_enseignement_translator,
        )

        cdd_president = []
        if settings.ESB_API_URL:
            try:
                cdd_president = MandatesService.get(
                    function=MandateFunctionEnum.PRESI,
                    entity_acronym=proposition_dto.formation.sigle_entite_gestion,
                )
            except MandatesException:
                pass

        return {
            'proposition': proposition_dto,
            'groupe_supervision': groupe_supervision_dto,
            'cdd_president': cdd_president[0] if cdd_president else None,
        }

    @classmethod
    @override(settings.LANGUAGE_CODE)
    def generer_attestation_refus_cdd(
        cls,
        proposition: Proposition,
        gestionnaire: PersonneConnueUclDTO,
        proposition_repository: IPropositionRepository,
        unites_enseignement_translator: IUnitesEnseignementTranslator,
    ) -> None:
        # Get the information to display on the pdf
        proposition_dto = proposition_repository.get_dto_for_gestionnaire(
            proposition.entity_id,
            unites_enseignement_translator,
        )

        cdd_decision_comment = CommentEntry.objects.filter(
            object_uuid=proposition_dto.uuid,
            tags=[OngletsChecklist.decision_cdd.name, 'CDD_FOR_SIC'],
        ).first()

        # Generate the pdf
        token = admission_generate_pdf(
            admission=None,
            template='admission/exports/cdd_refusal_certificate.html',
            filename='cdd_refusal_certificate.pdf',
            context={
                'proposition': proposition_dto,
                'manager': gestionnaire,
                'cdd_decision_comment': cdd_decision_comment,
            },
            stylesheets=WeasyprintStylesheets.get_stylesheets(),
            author=gestionnaire.matricule,
        )

        # Store the token of the pdf
        proposition.certificat_refus_cdd = [token]

    @classmethod
    @override(settings.LANGUAGE_CODE)
    def generer_attestation_accord_cdd(
        cls,
        proposition: Proposition,
        gestionnaire: PersonneConnueUclDTO,
        proposition_repository: IPropositionRepository,
        unites_enseignement_translator: IUnitesEnseignementTranslator,
        profil_candidat_translator: IProfilCandidatTranslator,
        titres_selectionnes: List[TitreAccesSelectionnable],
        annee_courante: int,
        experience_parcours_interne_translator: IExperienceParcoursInterneTranslator,
        groupe_supervision_dto: GroupeDeSupervisionDTO,
    ) -> None:
        # Get the information to display on the pdf
        context = cls.get_base_fac_decision_context(
            proposition_id=proposition.entity_id,
            proposition_repository=proposition_repository,
            unites_enseignement_translator=unites_enseignement_translator,
            groupe_supervision_dto=groupe_supervision_dto,
        )

        if proposition.type_admission == ChoixTypeAdmission.ADMISSION:
            template = 'admission/exports/cdd_approval_certificate_admission.html'
        else:
            template = 'admission/exports/cdd_approval_certificate_pre_admission.html'

        # Generate the pdf
        token = admission_generate_pdf(
            admission=None,
            template=template,
            filename='cdd_approval_certificate.pdf',
            context=context,
            author=gestionnaire.matricule,
        )

        # Store the token of the pdf
        proposition.certificat_approbation_cdd = [token]

    @classmethod
    def generer_sic_temporaire(
        cls,
        proposition_repository: IPropositionRepository,
        profil_candidat_translator: IProfilCandidatTranslator,
        campus_repository: IUclouvainCampusRepository,
        proposition: Proposition,
        gestionnaire: str,
        pdf: str,
    ) -> Optional[str]:
        if pdf == 'refus':
            return cls.generer_attestation_refus_sic(
                proposition_repository=proposition_repository,
                profil_candidat_translator=profil_candidat_translator,
                campus_repository=campus_repository,
                proposition=proposition,
                gestionnaire=gestionnaire,
                temporaire=True,
            )

        PDF_GENERATION_METHOD = {
            'accord': cls.generer_attestation_accord_sic,
            'accord_annexe': cls.generer_attestation_accord_annexe_sic,
        }

        pdf_generation_method = PDF_GENERATION_METHOD.get(pdf)
        if pdf_generation_method is None:
            raise PdfSicInconnu()
        return pdf_generation_method(
            proposition_repository=proposition_repository,
            profil_candidat_translator=profil_candidat_translator,
            proposition=proposition,
            gestionnaire=gestionnaire,
            temporaire=True,
        )

    @classmethod
    def generer_attestation_accord_sic(
        cls,
        proposition_repository: IPropositionRepository,
        profil_candidat_translator: IProfilCandidatTranslator,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        from infrastructure.messages_bus import message_bus_instance

        documents_resume: ResumeEtEmplacementsDocumentsPropositionDTO = message_bus_instance.invoke(
            RecupererResumeEtEmplacementsDocumentsPropositionQuery(
                uuid_proposition=str(proposition.entity_id.uuid),
                avec_document_libres=True,
            )
        )

        proposition_dto = documents_resume.resume.proposition

        experiences_curriculum_par_uuid: Dict[str, Union[ExperienceNonAcademiqueDTO, ExperienceAcademiqueDTO]] = {
            str(experience.uuid): experience
            for experience in itertools.chain(
                documents_resume.resume.curriculum.experiences_non_academiques,
                documents_resume.resume.curriculum.experiences_academiques,
            )
        }

        documents = documents_resume.emplacements_documents
        documents_names = []

        # Get the list of documents
        for document in documents:
            if document.est_a_reclamer:
                document_identifier = document.identifiant.split('.')

                if (
                    document_identifier[0] == OngletsDemande.CURRICULUM.name
                    and (document_identifier[-1] in CHAMPS_DOCUMENTS_EXPERIENCES_CURRICULUM)
                    and document_identifier[1] in experiences_curriculum_par_uuid
                ):
                    # For the curriculum experiences, we would like to get the name of the experience
                    documents_names.append(
                        '{document_label} : {cv_xp_label}. {document_communication}'.format(
                            document_label=document.libelle_langue_candidat,
                            cv_xp_label=experiences_curriculum_par_uuid[document_identifier[1]].titre_pdf_decision_sic,
                            document_communication=document.justification_gestionnaire,
                        )
                    )

                else:
                    documents_names.append(
                        '{document_label}. {document_communication}'.format(
                            document_label=document.libelle_langue_candidat,
                            document_communication=document.justification_gestionnaire,
                        )
                    )

        token = admission_generate_pdf(
            admission=None,
            template='admission/exports/sic_approval_certificate.html',
            filename=f'Autorisation_inscription_Dossier_{proposition_dto.reference}.pdf',
            stylesheets=WeasyprintStylesheets.get_stylesheets_bootstrap_5(),
            context={
                'proposition': proposition_dto,
                'profil_candidat_identification': documents_resume.resume.identification,
                'profil_candidat_coordonnees': documents_resume.resume.coordonnees,
                'documents_names': documents_names,
                'director': cls._get_sic_director(proposition_dto),
                'ORDERED_CAMPUSES_UUIDS': ORDERED_CAMPUSES_UUIDS,
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
        profil_candidat_translator: IProfilCandidatTranslator,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        from infrastructure.messages_bus import message_bus_instance

        with translation.override(settings.LANGUAGE_CODE_FR):
            proposition_dto = proposition_repository.get_dto_for_gestionnaire(
                proposition.entity_id, UnitesEnseignementTranslator
            )

            nombre_credits_formation = message_bus_instance.invoke(
                GetCreditsDeLaFormationQuery(
                    sigle=proposition_dto.formation.sigle,
                    annee=proposition_dto.formation.annee,
                )
            )

            if not proposition_dto.candidat_a_nationalite_hors_ue_5 and not temporaire:
                # The annex 1 must be generated only for H(UE+5) candidates
                proposition.certificat_approbation_sic_annexe = []
                return

            profil_candidat_identification = profil_candidat_translator.get_identification(
                proposition.matricule_candidat
            )
            token = admission_generate_pdf(
                admission=None,
                template='admission/exports/sic_approval_annexe.html',
                filename='Formulaire_pour_la_demande_de_visa.pdf',
                context={
                    'proposition': proposition_dto,
                    'profil_candidat_identification': profil_candidat_identification,
                    'rector': cls._get_sic_rector(),
                    'nombre_credits_formation': nombre_credits_formation,
                },
                stylesheets=WeasyprintStylesheets.get_stylesheets_bootstrap_5(),
                author=gestionnaire,
            )
        if temporaire:
            return token
        proposition.certificat_approbation_sic_annexe = [token]

    @classmethod
    def generer_attestation_refus_sic(
        cls,
        proposition_repository: IPropositionRepository,
        profil_candidat_translator: IProfilCandidatTranslator,
        campus_repository: IUclouvainCampusRepository,
        proposition: Proposition,
        gestionnaire: str,
        temporaire: bool = False,
    ) -> Optional[str]:
        if proposition.type_de_refus == TypeDeRefus.REFUS_LIBRE:
            return None

        with translation.override(settings.LANGUAGE_CODE_FR):
            proposition_dto = proposition_repository.get_dto_for_gestionnaire(
                proposition.entity_id, UnitesEnseignementTranslator
            )
            profil_candidat_identification = profil_candidat_translator.get_identification(
                proposition.matricule_candidat
            )
            profil_candidat_coordonnees = profil_candidat_translator.get_coordonnees(proposition.matricule_candidat)
            token = admission_generate_pdf(
                admission=None,
                template='admission/exports/sic_refusal_certificate.html',
                filename=f'UCLouvain_{proposition_dto.reference}.pdf',
                context={
                    'proposition': proposition_dto,
                    'profil_candidat_identification': profil_candidat_identification,
                    'profil_candidat_coordonnees': profil_candidat_coordonnees,
                    'director': cls._get_sic_director(proposition_dto),
                    'footer_campus': cls._get_refusal_certificate_footer_campus(proposition_dto, campus_repository),
                    'ORDERED_CAMPUSES_UUIDS': ORDERED_CAMPUSES_UUIDS,
                },
                author=gestionnaire,
            )
        if temporaire:
            return token
        proposition.certificat_refus_sic = [token]
