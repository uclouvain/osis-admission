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
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.commands import (
    SpecifierInformationsAcceptationPropositionParSicCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository


def specifier_informations_acceptation_proposition_par_sic(
    cmd: SpecifierInformationsAcceptationPropositionParSicCommand,
    proposition_repository: 'IPropositionRepository',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    # THEN
    proposition.specifier_informations_acceptation_par_sic(
        auteur_modification=cmd.gestionnaire,
        avec_conditions_complementaires=cmd.avec_conditions_complementaires,
        uuids_conditions_complementaires_existantes=cmd.uuids_conditions_complementaires_existantes,
        conditions_complementaires_libres=cmd.conditions_complementaires_libres,
        avec_complements_formation=cmd.avec_complements_formation,
        uuids_complements_formation=cmd.uuids_complements_formation,
        commentaire_complements_formation=cmd.commentaire_complements_formation,
        nombre_annees_prevoir_programme=cmd.nombre_annees_prevoir_programme,
        nom_personne_contact_programme_annuel=cmd.nom_personne_contact_programme_annuel,
        email_personne_contact_programme_annuel=cmd.email_personne_contact_programme_annuel,
        droits_inscription_montant=cmd.droits_inscription_montant,
        droits_inscription_montant_autre=cmd.droits_inscription_montant_autre,
        dispense_ou_droits_majores=cmd.dispense_ou_droits_majores,
        tarif_particulier=cmd.tarif_particulier,
        refacturation_ou_tiers_payant=cmd.refacturation_ou_tiers_payant,
        annee_de_premiere_inscription_et_statut=cmd.annee_de_premiere_inscription_et_statut,
        est_mobilite=cmd.est_mobilite,
        nombre_de_mois_de_mobilite=cmd.nombre_de_mois_de_mobilite,
        doit_se_presenter_en_sic=cmd.doit_se_presenter_en_sic,
        communication_au_candidat=cmd.communication_au_candidat,
    )

    proposition_repository.save(entity=proposition)

    return proposition.entity_id
