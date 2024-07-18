# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.commands import SoumettreTicketPersonneCommand
from admission.ddd.admission.domain.service.i_client_comptabilite_translator import IClientComptabiliteTranslator
from admission.ddd.admission.domain.service.i_digit import IDigitService
from admission.ddd.admission.domain.service.i_periode_soumission_ticket_digit import \
    IPeriodeSoumissionTicketDigitTranslator
from admission.ddd.admission.formation_generale.domain.service.i_formation import IFormationGeneraleTranslator
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.repository.i_digit import IDigitRepository
from ddd.logic.shared_kernel.signaletique_etudiant.domain.service.noma import NomaGenerateurService
from ddd.logic.shared_kernel.signaletique_etudiant.repository.i_compteur_noma import ICompteurAnnuelPourNomaRepository


def soumettre_ticket_creation_personne(
    cmd: 'SoumettreTicketPersonneCommand',
    digit_repository: 'IDigitRepository',
    digit_service: 'IDigitService',
    compteur_noma: 'ICompteurAnnuelPourNomaRepository',
    proposition_repository: 'IPropositionRepository',
    formation_translator: 'IFormationGeneraleTranslator',
    client_comptabilite_translator: 'IClientComptabiliteTranslator',
    periode_soumission_ticket_digit_translator: 'IPeriodeSoumissionTicketDigitTranslator'
) -> str:
    proposition = proposition_repository.get_first_submitted_proposition(matricule_candidat=cmd.global_id)
    digit_service.verifier_peut_soumettre_ticket_creation(proposition, periode_soumission_ticket_digit_translator)
    formation = formation_translator.get(entity_id=proposition.formation_id)

    sap_number = client_comptabilite_translator.get_client_number(matricule_candidat=cmd.global_id)

    noma = digit_repository.get_registration_id_sent_to_digit(global_id=cmd.global_id)
    if not noma:
        noma = NomaGenerateurService.generer_noma(
            compteur=compteur_noma.get_compteur(annee=cmd.annee).compteur,
            annee=cmd.annee,
        )
    extra_ticket_data = {'program_type': formation.type.name, 'sap_number': sap_number}
    return digit_repository.submit_person_ticket(
        global_id=cmd.global_id, noma=noma, extra_ticket_data=extra_ticket_data
    )
