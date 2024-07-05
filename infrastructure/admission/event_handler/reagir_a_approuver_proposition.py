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
from typing import Any, Union

from admission.ddd.admission.formation_generale.events import AdmissionApprouveeParSicEvent, \
    InscriptionApprouveeParSicEvent


def reagir_a_approuver_proposition(
    msg_bus: Any,
    event: Union['InscriptionApprouveeParSicEvent', 'AdmissionApprouveeParSicEvent'],
) -> None:
    from ddd.logic.shared_kernel.signaletique_etudiant.domain.service.noma import NomaGenerateurService
    from admission.infrastructure.admission.repository.digit import DigitRepository
    from infrastructure.shared_kernel.signaletique_etudiant.repository.compteur_noma import \
        CompteurAnnuelPourNomaRepository

    digit_repository = DigitRepository()
    compteur_noma = CompteurAnnuelPourNomaRepository()

    # send digit creation ticket if not sent yet
    if not digit_repository.has_digit_creation_ticket(global_id=event.matricule):
        noma = digit_repository.get_registration_id_sent_to_digit(global_id=event.matricule)
        if noma is None:
            noma = NomaGenerateurService.generer_noma(
                compteur=compteur_noma.get_compteur(annee=event.annee).compteur,
                annee=event.annee,
            )
        digit_repository.submit_person_ticket(
            global_id=event.matricule,
            noma=noma
        )
