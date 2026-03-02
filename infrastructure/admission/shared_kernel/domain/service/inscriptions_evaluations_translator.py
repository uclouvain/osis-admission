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
import datetime

from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_evaluations_translator import (
    IInscriptionsEvaluationsTranslator,
)
from ddd.logic.inscription_aux_evaluations.preparation_session.dto.periode_inscription_etudiant_calendrier_academique import (
    PeriodeInscriptionEtudiantCalendrierAcademiqueDTO,
)
from ddd.logic.inscription_aux_evaluations.preparation_session.queries import (
    RecupererPeriodeInscriptionEtudiantsCalendrierAcademiqueQuery,
)
from ddd.logic.inscription_aux_evaluations.shared_kernel.dto.formulaire_inscription import FormulaireInscriptionDTO
from ddd.logic.inscription_aux_evaluations.shared_kernel.queries import RechercherFormulairesQuery


class InscriptionsEvaluationsTranslator(IInscriptionsEvaluationsTranslator):
    def recuperer_date_fin_periode_inscription_etudiants_derniere_session(self, annee: int) -> datetime.date | None:
        from infrastructure.messages_bus import message_bus_instance

        periode: PeriodeInscriptionEtudiantCalendrierAcademiqueDTO = message_bus_instance.invoke(
            RecupererPeriodeInscriptionEtudiantsCalendrierAcademiqueQuery(annee=annee, session=3)
        )

        return periode.fin

    def recuperer_inscriptions_etudiants_derniere_session(self, nomas: list[str], annee: int) -> set[tuple[str, str]]:
        from infrastructure.messages_bus import message_bus_instance

        last_session_exam_enrolments: list[FormulaireInscriptionDTO] = message_bus_instance.invoke(
            RechercherFormulairesQuery(
                annee=annee,
                nomas=nomas,
                session=3,
            )
        )

        return {
            (exam_enrolment.noma, exam_enrolment.sigle_formation)
            for exam_enrolment in last_session_exam_enrolments
            if any(ue_enrolment.est_inscrit_evaluation for ue_enrolment in exam_enrolment.inscriptions)
        }
