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
import datetime
from typing import Optional, Dict, List

import attr

from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.formation_continue.domain.model._adresse import Adresse
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutProposition,
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
)
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PropositionIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Proposition(interface.RootEntity):
    entity_id: 'PropositionIdentity'
    formation_id: 'FormationIdentity'
    matricule_candidat: str
    reference: int
    annee_calculee: Optional[int] = None
    pot_calcule: Optional[AcademicCalendarTypes] = None
    statut: ChoixStatutProposition = ChoixStatutProposition.IN_PROGRESS

    creee_le: Optional[datetime.datetime] = None
    modifiee_le: Optional[datetime.datetime] = None
    soumise_le: Optional[datetime.datetime] = None

    reponses_questions_specifiques: Dict = attr.Factory(dict)

    curriculum: List[str] = attr.Factory(list)
    equivalence_diplome: List[str] = attr.Factory(list)
    elements_confirmation: Dict[str, str] = attr.Factory(dict)

    inscription_a_titre: Optional[ChoixInscriptionATitre] = None
    nom_siege_social: Optional[str] = ''
    numero_unique_entreprise: Optional[str] = ''
    numero_tva_entreprise: Optional[str] = ''
    adresse_mail_professionnelle: Optional[str] = ''
    type_adresse_facturation: Optional[ChoixTypeAdresseFacturation] = None
    adresse_facturation: Optional[Adresse] = None

    def modifier_choix_formation(self, formation_id: FormationIdentity, reponses_questions_specifiques: Dict):
        self.formation_id = formation_id
        self.reponses_questions_specifiques = reponses_questions_specifiques

    def supprimer(self):
        self.statut = ChoixStatutProposition.CANCELLED

    def soumettre(
        self,
        formation_id: FormationIdentity,
        pool: 'AcademicCalendarTypes',
        elements_confirmation: Dict[str, str],
    ):
        self.statut = ChoixStatutProposition.SUBMITTED
        self.annee_calculee = formation_id.annee
        self.formation_id = formation_id
        self.pot_calcule = pool
        self.elements_confirmation = elements_confirmation

    def completer_curriculum(
        self,
        curriculum: List[str],
        equivalence_diplome: List[str],
        reponses_questions_specifiques: Dict,
    ):
        self.curriculum = curriculum
        self.equivalence_diplome = equivalence_diplome
        self.reponses_questions_specifiques = reponses_questions_specifiques

    def completer_informations_complementaires(
        self,
        inscription_a_titre: Optional[str],
        nom_siege_social: Optional[str],
        numero_unique_entreprise: Optional[str],
        numero_tva_entreprise: Optional[str],
        adresse_mail_professionnelle: Optional[str],
        type_adresse_facturation: Optional[str],
        adresse_facturation_rue: Optional[str],
        adresse_facturation_numero_rue: Optional[str],
        adresse_facturation_code_postal: Optional[str],
        adresse_facturation_ville: Optional[str],
        adresse_facturation_pays: Optional[str],
        adresse_facturation_destinataire: Optional[str],
        adresse_facturation_boite_postale: Optional[str],
        adresse_facturation_lieu_dit: Optional[str],
        reponses_questions_specifiques: Dict,
    ):
        self.inscription_a_titre = ChoixInscriptionATitre[inscription_a_titre] if inscription_a_titre else None
        self.nom_siege_social = nom_siege_social or ''
        self.numero_unique_entreprise = numero_unique_entreprise or ''
        self.numero_tva_entreprise = numero_tva_entreprise or ''
        self.adresse_mail_professionnelle = adresse_mail_professionnelle or ''
        self.type_adresse_facturation = (
            ChoixTypeAdresseFacturation[type_adresse_facturation] if type_adresse_facturation else None
        )
        self.adresse_facturation = (
            Adresse(
                rue=adresse_facturation_rue or '',
                numero_rue=adresse_facturation_numero_rue or '',
                code_postal=adresse_facturation_code_postal or '',
                ville=adresse_facturation_ville or '',
                pays=adresse_facturation_pays or '',
                destinataire=adresse_facturation_destinataire,
                boite_postale=adresse_facturation_boite_postale,
                lieu_dit=adresse_facturation_lieu_dit,
            )
            if self.type_adresse_facturation == ChoixTypeAdresseFacturation.AUTRE
            else None
        )
        self.reponses_questions_specifiques = reponses_questions_specifiques
