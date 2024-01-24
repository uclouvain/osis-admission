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
from typing import Optional, Union, List

import attr
from django.utils.functional import cached_property

from admission.ddd.admission.doctorat.preparation import dtos as dtos_doctorat
from admission.ddd.admission.dtos import IdentificationDTO, CoordonneesDTO
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.formation_continue import dtos as dtos_formation_continue
from admission.ddd.admission.formation_generale import dtos as dtos_formation_generale
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import EtudesSecondairesDTO
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import CurriculumDTO
from osis_common.ddd import interface

AdmissionPropositionDTO = Union[
    dtos_doctorat.PropositionDTO,
    dtos_formation_continue.PropositionDTO,
    dtos_formation_generale.PropositionDTO,
]

AdmissionComptabiliteDTO = Union[
    dtos_doctorat.ComptabiliteDTO,
    dtos_formation_generale.ComptabiliteDTO,
]


@attr.dataclass(frozen=True, slots=True)
class ResumeCandidatDTO(interface.DTO):
    """
    DTO contenant l'ensemble des informations relatives à un candidat.
    """

    identification: IdentificationDTO
    coordonnees: CoordonneesDTO
    curriculum: CurriculumDTO
    etudes_secondaires: Optional[EtudesSecondairesDTO]
    connaissances_langues: Optional[List[dtos_doctorat.ConnaissanceLangueDTO]]


@attr.dataclass(frozen=True, slots=True)
class ResumePropositionDTO(ResumeCandidatDTO):
    """
    DTO contenant l'ensemble des informations relatives à la proposition et au candidat associé.
    """

    proposition: AdmissionPropositionDTO
    comptabilite: Optional[AdmissionComptabiliteDTO]
    groupe_supervision: Optional[dtos_doctorat.GroupeDeSupervisionDTO]

    @cached_property
    def est_proposition_doctorale(self):
        return isinstance(self.proposition, dtos_doctorat.PropositionDTO)

    @cached_property
    def est_proposition_continue(self):
        return isinstance(self.proposition, dtos_formation_continue.PropositionDTO)

    @cached_property
    def est_proposition_generale(self):
        return isinstance(self.proposition, dtos_formation_generale.PropositionDTO)


@attr.dataclass(frozen=True, slots=True)
class ResumeEtEmplacementsDocumentsPropositionDTO:
    """
    DTO contenant l'ensemble des informations relatives à la proposition et au candidat associé.
    """

    resume: ResumePropositionDTO
    emplacements_documents: List[EmplacementDocumentDTO]
