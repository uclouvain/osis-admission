# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

import attr

from ddd.logic.reference.domain.model.bourse import BourseIdentity
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class ParcoursDoctoral(interface.ValueObject):
    uuid: str
    matricule_doctorant: str

    justification: str
    commission_proximite: str

    financement_type: str
    financement_type_contrat_travail: str
    financement_eft: Optional[int]
    financement_bourse_recherche: Optional[BourseIdentity]
    financement_autre_bourse_recherche: str
    financement_bourse_date_debut: Optional[datetime.date]
    financement_bourse_date_fin: Optional[datetime.date]
    financement_bourse_preuve: List[str]
    financement_duree_prevue: Optional[int]
    financement_temps_consacre: Optional[int]
    financement_est_lie_fnrs_fria_fresh_csc: Optional[bool]
    financement_commentaire: str

    projet_langue_redaction_these: str
    projet_institut_these: str
    projet_lieu_these: str
    projet_titre: str
    projet_resume: str
    projet_doctorat_deja_realise: str
    projet_institution: str
    projet_domaine_these: str
    projet_date_soutenance: Optional[datetime.date]
    projet_raison_non_soutenue: str
    projet_projet_doctoral_deja_commence: Optional[bool]
    projet_projet_doctoral_institution: str
    projet_projet_doctoral_date_debut: Optional[datetime.date]
    projet_documents_projet: List[str]
    projet_graphe_gantt: List[str]
    projet_proposition_programme_doctoral: List[str]
    projet_projet_formation_complementaire: List[str]
    projet_lettres_recommandation: List[str]
