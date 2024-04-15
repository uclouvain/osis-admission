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
from functools import partial
from typing import List

from admission.calendar.admission_calendar import DIPLOMES_ACCES_BELGE
from admission.ddd.admission.domain.model.formation import Formation
from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifique
from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.domain.service.i_maximum_propositions import IMaximumPropositionsAutorisees
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces, Titres
from admission.ddd.admission.domain.service.profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.service.verifier_questions_specifiques import VerifierQuestionsSpecifiques
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_formation import IFormationGeneraleTranslator
from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
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
        annee_soumise: int = None,
        pool_soumis: 'AcademicCalendarTypes' = None,
    ) -> None:
        profil_candidat_service = ProfilCandidat()
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
                profil_candidat_service.verifier_etudes_secondaires,
                matricule=proposition_candidat.matricule_candidat,
                formation=formation,
                profil_candidat_translator=profil_candidat_translator,
            ),
            partial(
                profil_candidat_service.verifier_curriculum_formation_generale,
                proposition_candidat,
                formation.type,
                profil_candidat_translator,
                annee_courante,
            ),
            partial(
                VerifierQuestionsSpecifiques.verifier_onglet_curriculum,
                proposition_candidat,
                questions_specifiques,
            ),
            partial(
                profil_candidat_service.verifier_comptabilite_formation_generale,
                proposition_candidat,
                profil_candidat_translator,
                annee_courante,
                formation,
            ),
            partial(
                profil_candidat_service.verifier_informations_complementaires_formation_generale,
                proposition=proposition_candidat,
                profil_candidat_translator=profil_candidat_translator,
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
                type_formation=formation.type,
                profil_candidat_translator=profil_candidat_translator,
                formation_translator=formation_translator,
                annee_soumise=annee_soumise,
                pool_soumis=pool_soumis,
            ),
            partial(
                maximum_propositions_service.verifier_nombre_propositions_envoyees_formation_generale,
                matricule=proposition_candidat.matricule_candidat,
            ),
        )

    @classmethod
    def determiner_type_demande(
        cls,
        proposition: 'Proposition',
        titres: 'Titres',
        calendrier_inscription: 'ICalendrierInscription',
        profil_candidat_translator: 'IProfilCandidatTranslator',
    ) -> 'TypeDemande':
        # (Nationalité UE+5)
        #   ET (tous les diplômes belges (y compris secondaires si déclaré dans le détail)) = inscription
        est_ue_plus_5 = calendrier_inscription.est_ue_plus_5(
            profil_candidat_translator.get_identification(proposition.matricule_candidat),
            situation_assimilation=None,  # ne pas prendre en compte le critère d'assimilation
        )
        diplomes_tous_belge = set(titres.get_valid_conditions()) <= set(DIPLOMES_ACCES_BELGE)
        return TypeDemande.INSCRIPTION if est_ue_plus_5 and diplomes_tous_belge else TypeDemande.ADMISSION
