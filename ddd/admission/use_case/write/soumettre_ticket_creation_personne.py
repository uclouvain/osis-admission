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
from admission.ddd.admission.repository.i_digit import IDigitRepository
from ddd.logic.shared_kernel.signaletique_etudiant.domain.service.noma import NomaGenerateurService
from ddd.logic.shared_kernel.signaletique_etudiant.repository.i_compteur_noma import ICompteurAnnuelPourNomaRepository


def soumettre_ticket_creation_personne(
    cmd: 'SoumettreTicketPersonneCommand',
    digit_repository: 'IDigitRepository',
    compteur_noma: 'ICompteurAnnuelPourNomaRepository',
) -> any:
    noma = NomaGenerateurService.generer_noma(
        compteur=compteur_noma.get_compteur(annee=cmd.annee).compteur,
        annee=cmd.annee
    )
    return digit_repository.submit_person_ticket(global_id=cmd.global_id, noma=noma)
