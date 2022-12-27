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
import datetime

from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.domain.service.i_elements_confirmation import IElementsConfirmation
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.enums.question_specifique import Onglets
from admission.ddd.admission.formation_generale.commands import SoumettrePropositionCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_formation import IFormationGeneraleTranslator
from admission.ddd.admission.formation_generale.domain.service.i_notification import INotification
from admission.ddd.admission.formation_generale.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.formation_generale.domain.service.verifier_proposition import VerifierProposition
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository


def soumettre_proposition(
    cmd: 'SoumettrePropositionCommand',
    proposition_repository: 'IPropositionRepository',
    formation_translator: 'IFormationGeneraleTranslator',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    titres_acces: 'ITitresAcces',
    calendrier_inscription: 'ICalendrierInscription',
    academic_year_repository: 'IAcademicYearRepository',
    questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
    element_confirmation: 'IElementsConfirmation',
    notification: 'INotification',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)
    annee_courante = (
        GetCurrentAcademicYear()
        .get_starting_academic_year(
            datetime.date.today(),
            academic_year_repository,
        )
        .year
    )
    questions_specifiques = questions_specifiques_translator.search_by_proposition(
        cmd.uuid_proposition,
        onglets=Onglets.get_names(),
    )

    # WHEN
    VerifierProposition().verifier(
        proposition_candidat=proposition,
        formation_translator=formation_translator,
        titres_acces=titres_acces,
        profil_candidat_translator=profil_candidat_translator,
        calendrier_inscription=calendrier_inscription,
        annee_courante=annee_courante,
        questions_specifiques=questions_specifiques,
        annee_soumise=cmd.annee,
        pool_soumis=AcademicCalendarTypes[cmd.pool],
    )
    element_confirmation.valider(
        soumis=cmd.elements_confirmation,
        proposition=proposition,
        formation_translator=formation_translator,
        profil_candidat_translator=profil_candidat_translator,
    )

    # THEN
    proposition.soumettre(cmd.annee, AcademicCalendarTypes[cmd.pool], cmd.elements_confirmation)
    proposition_repository.save(proposition)
    notification.confirmer_soumission(proposition)

    return proposition_id
