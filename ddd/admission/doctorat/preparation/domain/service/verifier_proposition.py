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
from functools import partial
from typing import List

from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import GroupeDeSupervision
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifique
from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.domain.service.i_maximum_propositions import IMaximumPropositionsAutorisees
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.domain.service.profil_candidat import ProfilCandidat
from admission.ddd.admission.domain.service.verifier_questions_specifiques import VerifierQuestionsSpecifiques
from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from osis_common.ddd import interface


class VerifierProposition(interface.DomainService):
    @classmethod
    def verifier(
        cls,
        proposition_candidat: 'Proposition',
        groupe_de_supervision: 'GroupeDeSupervision',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int,
        titres_acces: 'ITitresAcces',
        questions_specifiques: List['QuestionSpecifique'],
        formation_translator: 'IDoctoratTranslator',
        calendrier_inscription: 'ICalendrierInscription',
        maximum_propositions_service: 'IMaximumPropositionsAutorisees',
        annee_soumise: int = None,
        pool_soumis: 'AcademicCalendarTypes' = None,
    ) -> None:
        profil_candidat_service = ProfilCandidat()
        doctorat_id = proposition_candidat.formation_id
        titres = titres_acces.recuperer_titres_access(proposition_candidat.matricule_candidat, TrainingType.PHD)
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
            ),
            groupe_de_supervision.verifier_tout_le_monde_a_approuve,
            partial(
                profil_candidat_service.verifier_comptabilite_doctorat,
                proposition=proposition_candidat,
                profil_candidat_translator=profil_candidat_translator,
                annee_courante=annee_courante,
            ),
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
                titres_acces.verifier_titres,
                titres=titres,
            ),
            partial(
                calendrier_inscription.verifier,
                formation_id=doctorat_id,
                proposition=None,
                matricule_candidat=proposition_candidat.matricule_candidat,
                titres_acces=titres,
                type_formation=TrainingType.PHD,
                profil_candidat_translator=profil_candidat_translator,
                formation_translator=formation_translator,
                annee_soumise=annee_soumise,
                pool_soumis=pool_soumis,
            ),
            partial(
                maximum_propositions_service.verifier_nombre_propositions_envoyees_formation_doctorale,
                matricule=proposition_candidat.matricule_candidat,
            ),
        )
