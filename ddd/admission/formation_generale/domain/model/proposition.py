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
from typing import Dict, Optional, List

import attr

from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.domain.service.i_bourse import BourseIdentity
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutProposition
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

    creee_le: Optional[datetime.datetime] = None
    modifiee_le: Optional[datetime.datetime] = None

    bourse_double_diplome_id: Optional[BourseIdentity] = None
    bourse_internationale_id: Optional[BourseIdentity] = None
    bourse_erasmus_mundus_id: Optional[BourseIdentity] = None

    est_bachelier_belge: Optional[bool] = None
    est_reorientation_inscription_externe: Optional[bool] = None
    attestation_inscription_reguliere: List[str] = attr.Factory(list)

    est_modification_inscription_externe: Optional[bool] = None
    formulaire_modification_inscription: List[str] = attr.Factory(list)

    est_non_resident_au_sens_decret: Optional[bool] = None

    reponses_questions_specifiques: Dict = attr.Factory(dict)

    continuation_cycle_bachelier: Optional[bool] = None
    attestation_continuation_cycle_bachelier: List[str] = attr.Factory(list)
    curriculum: List[str] = attr.Factory(list)
    equivalence_diplome: List[str] = attr.Factory(list)

    def modifier_choix_formation(
        self,
        formation_id: FormationIdentity,
        bourses_ids: Dict[str, BourseIdentity],
        bourse_double_diplome: Optional[str],
        bourse_internationale: Optional[str],
        bourse_erasmus_mundus: Optional[str],
        reponses_questions_specifiques: Dict,
    ):
        self.formation_id = formation_id
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.bourse_double_diplome_id = bourses_ids.get(bourse_double_diplome) if bourse_double_diplome else None
        self.bourse_internationale_id = bourses_ids.get(bourse_internationale) if bourse_internationale else None
        self.bourse_erasmus_mundus_id = bourses_ids.get(bourse_erasmus_mundus) if bourse_erasmus_mundus else None

    def supprimer(self):
        self.statut = ChoixStatutProposition.CANCELLED

    def soumettre(self, annee: int, pool: 'AcademicCalendarTypes'):
        self.statut = ChoixStatutProposition.SUBMITTED
        self.annee_calculee = annee
        self.pot_calcule = pool
        if pool != AcademicCalendarTypes.ADMISSION_POOL_NON_RESIDENT_QUOTA:
            self.est_non_resident_au_sens_decret = None
        if pool not in [
            AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE,
            AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_ENROLLMENT_CHANGE,
        ]:
            self.est_bachelier_belge = None
        if pool != AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE:
            self.est_reorientation_inscription_externe = None
            self.attestation_inscription_reguliere = []
        if pool != AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_ENROLLMENT_CHANGE:
            self.est_modification_inscription_externe = None
            self.formulaire_modification_inscription = []

    def completer_curriculum(
        self,
        continuation_cycle_bachelier: Optional[bool],
        attestation_continuation_cycle_bachelier: List[str],
        curriculum: List[str],
        equivalence_diplome: List[str],
        reponses_questions_specifiques: Dict,
    ):
        self.continuation_cycle_bachelier = continuation_cycle_bachelier
        self.attestation_continuation_cycle_bachelier = attestation_continuation_cycle_bachelier
        self.curriculum = curriculum
        self.equivalence_diplome = equivalence_diplome
        self.reponses_questions_specifiques = reponses_questions_specifiques
