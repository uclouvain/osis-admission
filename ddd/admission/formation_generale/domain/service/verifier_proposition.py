# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial
from typing import List

from admission.calendar.admission_calendar import DIPLOMES_ACCES_BELGE
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition,
)
from admission.ddd.admission.formation_generale.domain.service.i_formation import (
    IFormationGeneraleTranslator,
)
from admission.ddd.admission.shared_kernel.domain.model.assimilation import Assimilation
from admission.ddd.admission.shared_kernel.domain.model.formation import Formation
from admission.ddd.admission.shared_kernel.domain.model.question_specifique import (
    QuestionSpecifique,
)
from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_calendrier_inscription import (
    ICalendrierInscription,
)
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_diffusion_notes_translator import IDiffusionNotesTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_evaluations_translator import (
    IInscriptionsEvaluationsTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.domain.service.i_maximum_propositions import (
    IMaximumPropositionsAutorisees,
)
from admission.ddd.admission.shared_kernel.domain.service.i_noma_translator import INomasTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_titres_acces import (
    ITitresAcces,
    Titres,
)
from admission.ddd.admission.shared_kernel.domain.service.profil_candidat import (
    ProfilCandidat,
)
from admission.ddd.admission.shared_kernel.domain.service.verifier_questions_specifiques import (
    VerifierQuestionsSpecifiques,
)
from admission.ddd.admission.shared_kernel.enums.type_demande import TypeDemande
from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
)
from osis_common.ddd import interface


class VerifierProposition(interface.DomainService):
    @classmethod
    def verifier(
        cls,
        proposition_candidat: 'Proposition',
        formation_translator: 'IFormationGeneraleTranslator',
        titres_acces: 'ITitresAcces',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        calendrier_inscription: 'ICalendrierInscription',
        annee_courante: int,
        questions_specifiques: List[QuestionSpecifique],
        maximum_propositions_service: 'IMaximumPropositionsAutorisees',
        titres: 'Titres',
        formation: 'Formation',
        annee_formation: AcademicYear,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
        inscriptions_translator: IInscriptionsTranslatorService,
        deliberation_translator: IDeliberationTranslator,
        diffusion_notes_translator: IDiffusionNotesTranslator,
        inscriptions_evaluations_translator: IInscriptionsEvaluationsTranslator,
        nomas_translator: INomasTranslator,
        candidat_est_inscrit_recemment_ucl: bool,
        candidat_est_en_poursuite_directe: bool,
        assimilation_passee: Assimilation | None,
        annee_soumise: int = None,
        pool_soumis: 'AcademicCalendarTypes' = None,
    ) -> None:
        profil_candidat_service = ProfilCandidat()

        curriculum = profil_candidat_translator.get_curriculum(
            matricule=proposition_candidat.matricule_candidat,
            annee_courante=annee_courante,
            uuid_proposition=proposition_candidat.entity_id.uuid,
            inscriptions_translator=inscriptions_translator,
        )

        execute_functions_and_aggregate_exceptions(
            partial(
                profil_candidat_service.verifier_identification,
                matricule=proposition_candidat.matricule_candidat,
                profil_candidat_translator=profil_candidat_translator,
                candidat_est_inscrit_recemment_ucl=candidat_est_inscrit_recemment_ucl,
            ),
            partial(
                profil_candidat_service.verifier_coordonnees,
                matricule=proposition_candidat.matricule_candidat,
                profil_candidat_translator=profil_candidat_translator,
            ),
            partial(
                profil_candidat_service.verifier_etudes_secondaires,
                matricule=proposition_candidat.matricule_candidat,
                formation=formation,
                profil_candidat_translator=profil_candidat_translator,
                candidat_est_inscrit_recemment_ucl=candidat_est_inscrit_recemment_ucl,
            ),
            partial(
                profil_candidat_service.verifier_examens,
                uuid_proposition=proposition_candidat.entity_id.uuid,
                matricule=proposition_candidat.matricule_candidat,
                sigle_formation=formation.entity_id.sigle,
                annee_formation=formation.entity_id.annee,
                profil_candidat_translator=profil_candidat_translator,
                candidat_est_en_poursuite=proposition_candidat.est_en_poursuite,
            ),
            partial(
                profil_candidat_service.verifier_curriculum_formation_generale,
                proposition_candidat,
                formation.type,
                annee_courante,
                annee_formation=annee_formation,
                curriculum=curriculum,
                candidat_est_inscrit_recemment_ucl=candidat_est_inscrit_recemment_ucl,
            ),
            partial(
                VerifierQuestionsSpecifiques.verifier_onglet_curriculum,
                proposition_candidat,
                questions_specifiques,
            ),
            partial(
                profil_candidat_service.verifier_comptabilite_formation_generale,
                proposition=proposition_candidat,
                profil_candidat_translator=profil_candidat_translator,
                annee_courante=annee_courante,
                formation=formation,
                inscriptions_translator=inscriptions_translator,
                assimilation_passee=assimilation_passee,
            ),
            partial(
                profil_candidat_service.verifier_choix_formation_generale,
                proposition=proposition_candidat,
                formation=formation,
                annee_inscription_formation_translator=annee_inscription_formation_translator,
                inscriptions_translator=inscriptions_translator,
                deliberation_translator=deliberation_translator,
                diffusion_notes_translator=diffusion_notes_translator,
                inscriptions_evaluations_translator=inscriptions_evaluations_translator,
                nomas_translator=nomas_translator,
            ),
            partial(
                profil_candidat_service.verifier_informations_complementaires_formation_generale,
                proposition=proposition_candidat,
                profil_candidat_translator=profil_candidat_translator,
                experiences_academiques=curriculum.experiences_academiques,
                formation=formation,
                candidat_est_inscrit_recemment_ucl=candidat_est_inscrit_recemment_ucl,
            ),
            partial(
                VerifierQuestionsSpecifiques.verifier_onglet_etudes_secondaires,
                proposition_candidat,
                questions_specifiques,
            ),
            partial(
                VerifierQuestionsSpecifiques.verifier_onglet_questions_specifiques,
                proposition_candidat,
                questions_specifiques,
            ),
            partial(
                VerifierQuestionsSpecifiques.verifier_onglet_choix_formation,
                proposition_candidat,
                questions_specifiques,
            ),
            partial(
                titres_acces.verifier_titres,
                titres=titres,
            ),
            partial(
                calendrier_inscription.verifier,
                formation_id=proposition_candidat.formation_id,
                proposition=proposition_candidat,
                matricule_candidat=proposition_candidat.matricule_candidat,
                titres_acces=titres,
                profil_candidat_translator=profil_candidat_translator,
                formation_translator=formation_translator,
                annee_soumise=annee_soumise,
                pool_soumis=pool_soumis,
                formation=formation,
                candidat_est_en_poursuite_directe=candidat_est_en_poursuite_directe,
                inscriptions_translator=inscriptions_translator,
            ),
            partial(
                maximum_propositions_service.verifier_nombre_propositions_envoyees_formation_generale,
                proposition_candidat=proposition_candidat,
                profil_candidat_translator=profil_candidat_translator,
                annee_soumise=annee_soumise,
            ),
            partial(
                maximum_propositions_service.verifier_une_seule_demande_envoyee_par_formation_generale_par_annee,
                proposition_candidat=proposition_candidat,
                annee_soumise=annee_soumise,
            ),
        )

    @classmethod
    def determiner_type_demande(
        cls,
        proposition: 'Proposition',
        titres: 'Titres',
        calendrier_inscription: 'ICalendrierInscription',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        candidat_est_inscrit_recemment_ucl: bool,
    ) -> 'TypeDemande':
        est_ue_plus_5 = calendrier_inscription.est_ue_plus_5(
            profil_candidat_translator.get_identification(proposition.matricule_candidat),
        )
        if candidat_est_inscrit_recemment_ucl:
            # Hors (UE+5) qui ne sont pas en poursuite = admission
            # le reste = inscription
            return (
                TypeDemande.ADMISSION
                if not est_ue_plus_5 and not proposition.est_en_poursuite
                else TypeDemande.INSCRIPTION
            )
        else:
            # (Nationalité UE+5)
            #   ET (tous les diplômes belges (y compris secondaires si déclaré dans le détail)) = inscription
            diplomes_tous_belge = set(titres.get_valid_conditions()) <= set(DIPLOMES_ACCES_BELGE)
            return TypeDemande.INSCRIPTION if est_ue_plus_5 and diplomes_tous_belge else TypeDemande.ADMISSION
