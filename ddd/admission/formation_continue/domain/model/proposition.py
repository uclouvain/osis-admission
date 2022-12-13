##############################################################################
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
##############################################################################
import datetime
from typing import Optional, Dict, List

import attr

from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.enums import (
    TypeSituationAssimilation,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    LienParente,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixAffiliationSport,
    ChoixTypeCompteBancaire,
)
from admission.ddd.admission.formation_continue.domain.model._comptabilite import comptabilite_non_remplie, Comptabilite
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutProposition
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
    annee_calculee: Optional[int] = None
    pot_calcule: Optional[AcademicCalendarTypes] = None
    statut: ChoixStatutProposition = ChoixStatutProposition.IN_PROGRESS
    comptabilite: 'Comptabilite' = comptabilite_non_remplie

    creee_le: Optional[datetime.datetime] = None
    modifiee_le: Optional[datetime.datetime] = None

    reponses_questions_specifiques: Dict = attr.Factory(dict)

    curriculum: List[str] = attr.Factory(list)
    equivalence_diplome: List[str] = attr.Factory(list)

    def modifier_choix_formation(self, formation_id: FormationIdentity, reponses_questions_specifiques: Dict):
        self.formation_id = formation_id
        self.reponses_questions_specifiques = reponses_questions_specifiques

    def supprimer(self):
        self.statut = ChoixStatutProposition.CANCELLED

    def soumettre(self, annee: int, pool: 'AcademicCalendarTypes'):
        self.statut = ChoixStatutProposition.SUBMITTED
        self.annee_calculee = annee
        self.pot_calcule = pool

    def completer_curriculum(
        self,
        curriculum: List[str],
        equivalence_diplome: List[str],
        reponses_questions_specifiques: Dict,
    ):
        self.curriculum = curriculum
        self.equivalence_diplome = equivalence_diplome
        self.reponses_questions_specifiques = reponses_questions_specifiques

    def completer_comptabilite(
        self,
        etudiant_solidaire: Optional[bool],
        type_numero_compte: Optional[str],
        numero_compte_iban: Optional[str],
        iban_valide: Optional[bool],
        numero_compte_autre_format: Optional[str],
        code_bic_swift_banque: Optional[str],
        prenom_titulaire_compte: Optional[str],
        nom_titulaire_compte: Optional[str],
    ):
        self.comptabilite = Comptabilite(
            etudiant_solidaire=etudiant_solidaire,
            type_numero_compte=ChoixTypeCompteBancaire[type_numero_compte] if type_numero_compte else None,
            numero_compte_iban=numero_compte_iban,
            iban_valide=iban_valide,
            numero_compte_autre_format=numero_compte_autre_format,
            code_bic_swift_banque=code_bic_swift_banque,
            prenom_titulaire_compte=prenom_titulaire_compte,
            nom_titulaire_compte=nom_titulaire_compte,
        )
