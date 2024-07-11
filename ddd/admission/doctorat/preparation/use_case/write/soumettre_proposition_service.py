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
import datetime

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import SoumettrePropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import INotification
from admission.ddd.admission.doctorat.preparation.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.doctorat.preparation.domain.service.verifier_proposition import VerifierProposition
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.doctorat.validation.domain.service.demande import DemandeService
from admission.ddd.admission.doctorat.validation.repository.i_demande import IDemandeRepository
from admission.ddd.admission.domain.builder.formation_identity import FormationIdentityBuilder
from admission.ddd.admission.domain.service.i_calendrier_inscription import ICalendrierInscription
from admission.ddd.admission.domain.service.i_elements_confirmation import IElementsConfirmation
from admission.ddd.admission.domain.service.i_maximum_propositions import IMaximumPropositionsAutorisees
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.enums.question_specifique import Onglets
from admission.ddd.admission.domain.service.profil_soumis_candidat import (
    ProfilSoumisCandidatTranslator,
)
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository


def soumettre_proposition(
    cmd: 'SoumettrePropositionCommand',
    proposition_repository: 'IPropositionRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    demande_repository: 'IDemandeRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    historique: 'IHistorique',
    notification: 'INotification',
    titres_acces: 'ITitresAcces',
    questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
    doctorat_translator: 'IDoctoratTranslator',
    calendrier_inscription: 'ICalendrierInscription',
    element_confirmation: 'IElementsConfirmation',
    maximum_propositions_service: 'IMaximumPropositionsAutorisees',
) -> 'PropositionIdentity':
    # GIVEN
    proposition_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition = proposition_repository.get(entity_id=proposition_id)
    groupe_supervision = groupe_supervision_repository.get_by_proposition_id(proposition_id)
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
        onglets=[
            Onglets.CURRICULUM.name,
            Onglets.ETUDES_SECONDAIRES.name,
        ],
    )
    formation = doctorat_translator.get(proposition.formation_id.sigle, proposition.formation_id.annee)
    formation_id = FormationIdentityBuilder.build(sigle=proposition.formation_id.sigle, annee=cmd.annee)
    titres = titres_acces.recuperer_titres_access(
        proposition.matricule_candidat,
        formation.type,
    )
    type_demande = VerifierProposition.determiner_type_demande(
        proposition,
        titres,
        calendrier_inscription,
        profil_candidat_translator,
    )

    # WHEN
    VerifierProposition().verifier(
        proposition_candidat=proposition,
        groupe_de_supervision=groupe_supervision,
        profil_candidat_translator=profil_candidat_translator,
        annee_courante=annee_courante,
        titres_acces=titres_acces,
        questions_specifiques=questions_specifiques,
        formation_translator=doctorat_translator,
        calendrier_inscription=calendrier_inscription,
        maximum_propositions_service=maximum_propositions_service,
        annee_soumise=cmd.annee,
        pool_soumis=AcademicCalendarTypes[cmd.pool],
    )
    element_confirmation.valider(
        cmd.elements_confirmation,
        proposition=proposition,
        annee_soumise=cmd.annee,
        formation_translator=doctorat_translator,
        profil_candidat_translator=profil_candidat_translator,
    )

    profil_candidat_soumis = ProfilSoumisCandidatTranslator().recuperer(
        profil_candidat_translator=profil_candidat_translator,
        matricule_candidat=proposition.matricule_candidat,
    )

    demande = DemandeService().initier(
        proposition_id=proposition_id,
        type_admission=proposition.type_admission,
        profil_soumis_candidat=profil_candidat_soumis,
    )

    # THEN
    proposition.finaliser(
        formation_id=formation_id,
        type_demande=type_demande,
        pool=AcademicCalendarTypes[cmd.pool],
        elements_confirmation=cmd.elements_confirmation,
    )
    proposition_repository.save(proposition)
    demande_repository.save(demande)
    historique.historiser_soumission(proposition)
    notification.notifier_soumission(proposition)

    return proposition_id
