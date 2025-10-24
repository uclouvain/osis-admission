# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial
from typing import List

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import (
    IPromoteurTranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.verifier_cotutelle import (
    CotutellePossedePromoteurExterne,
)
from admission.ddd.admission.doctorat.preparation.domain.service.verifier_promoteur import (
    GroupeDeSupervisionPossedeUnPromoteurMinimum,
)
from admission.ddd.admission.shared_kernel.domain.model.question_specifique import (
    QuestionSpecifique,
)
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.profil_candidat import (
    ProfilCandidat,
)
from admission.ddd.admission.shared_kernel.domain.service.verifier_questions_specifiques import (
    VerifierQuestionsSpecifiques,
)
from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
)
from osis_common.ddd import interface


class VerifierPropositionProjetDoctoral(interface.DomainService):
    @classmethod
    def verifier(
        cls,
        proposition_candidat: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        questions_specifiques: List[QuestionSpecifique],
        promoteur_translator: IPromoteurTranslator,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int,
        annee_formation: AcademicYear,
    ) -> None:
        # Les vérifications sont limitées à ce qui est modifiable par le candidat dans ce statut
        if proposition_candidat.statut in {
            ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE,
            ChoixStatutPropositionDoctorale.CA_EN_ATTENTE_DE_SIGNATURE,
        }:
            return

        if proposition_candidat.statut == ChoixStatutPropositionDoctorale.CA_A_COMPLETER:
            fonctions_verification = []

            if proposition_candidat.type_admission == ChoixTypeAdmission.ADMISSION:
                fonctions_verification.append(groupe_de_supervision.verifier_signataires_membres_ca)

            execute_functions_and_aggregate_exceptions(*fonctions_verification)

            return

        profil_candidat_service = ProfilCandidat()
        if proposition_candidat.type_admission == ChoixTypeAdmission.PRE_ADMISSION:
            fonctions_personnalisees = [
                # Vérification différente de la composition du groupe de supervision
                groupe_de_supervision.verifier_signataires_pre_admission,
            ]
        else:
            fonctions_personnalisees = [
                # Vérification différente de la composition du groupe de supervision
                groupe_de_supervision.verifier_signataires,
                # Vérification de la cotutelle, absente en pré-admission
                groupe_de_supervision.verifier_cotutelle,
                partial(CotutellePossedePromoteurExterne.verifier, groupe_de_supervision, promoteur_translator),
            ]

        execute_functions_and_aggregate_exceptions(
            partial(
                profil_candidat_service.verifier_identification,
                matricule=proposition_candidat.matricule_candidat,
                profil_candidat_translator=profil_candidat_translator,
            ),
            partial(
                profil_candidat_service.verifier_coordonnees,
                matricule=proposition_candidat.matricule_candidat,
                profil_candidat_translator=profil_candidat_translator,
            ),
            partial(
                profil_candidat_service.verifier_langues_connues,
                matricule=proposition_candidat.matricule_candidat,
                profil_candidat_translator=profil_candidat_translator,
            ),
            partial(
                profil_candidat_service.verifier_curriculum,
                matricule=proposition_candidat.matricule_candidat,
                profil_candidat_translator=profil_candidat_translator,
                annee_courante=annee_courante,
                curriculum_pdf=proposition_candidat.curriculum,
                uuid_proposition=proposition_candidat.entity_id.uuid,
                annee_formation=annee_formation,
            ),
            proposition_candidat.verifier_projet_doctoral,
            partial(GroupeDeSupervisionPossedeUnPromoteurMinimum.verifier, groupe_de_supervision, promoteur_translator),
            partial(
                VerifierQuestionsSpecifiques.verifier_onglet_curriculum,
                proposition=proposition_candidat,
                questions_specifiques=questions_specifiques,
            ),
            partial(
                VerifierQuestionsSpecifiques.verifier_onglet_etudes_secondaires,
                proposition=proposition_candidat,
                questions_specifiques=questions_specifiques,
            ),
            partial(
                VerifierQuestionsSpecifiques.verifier_onglet_choix_formation,
                proposition_candidat,
                questions_specifiques,
            ),
            *fonctions_personnalisees,
        )
