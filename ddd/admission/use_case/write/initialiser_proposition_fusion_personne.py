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
from admission.ddd.admission.commands import InitialiserPropositionFusionPersonneCommand
from admission.ddd.admission.domain.model.proposition_fusion_personne import PropositionFusionPersonneIdentity
from admission.ddd.admission.events import PropositionFusionInitialiseeEvent
from admission.ddd.admission.repository.i_proposition_fusion_personne import IPropositionPersonneFusionRepository


def initialiser_proposition_fusion_personne(
    msg_bus,
    cmd: 'InitialiserPropositionFusionPersonneCommand',
    proposition_fusion_personne_repository: 'IPropositionPersonneFusionRepository',
) -> PropositionFusionPersonneIdentity:
    proposition_fusion_personne_identity = proposition_fusion_personne_repository.initialiser(
        existing_merge_person_id=cmd.existing_merge_person_id,
        status=cmd.status,
        global_id=cmd.original_global_id,
        selected_global_id=cmd.selected_global_id,
        nom=cmd.nom,
        prenom=cmd.prenom,
        autres_prenoms=cmd.autres_prenoms,
        date_naissance=cmd.date_naissance,
        lieu_naissance=cmd.lieu_naissance,
        email=cmd.email,
        genre=cmd.genre,
        sex=cmd.sex,
        etat_civil=cmd.etat_civil,
        nationalite=cmd.nationalite,
        numero_national=cmd.numero_national,
        numero_carte_id=cmd.numero_carte_id,
        numero_passeport=cmd.numero_passeport,
        dernier_noma_connu=cmd.dernier_noma_connu,
        expiration_carte_id=cmd.expiration_carte_id,
        expiration_passeport=cmd.expiration_passeport,
        educational_curex_ids=cmd.educational_curex_uuids,
        professional_curex_ids=cmd.professional_curex_uuids,
    )
    msg_bus.publish(
        PropositionFusionInitialiseeEvent(
            entity_id=proposition_fusion_personne_identity,
            matricule=cmd.original_global_id,
        )
    )
    return proposition_fusion_personne_identity
