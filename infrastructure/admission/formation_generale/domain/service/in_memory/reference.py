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
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.i_reference import IReferenceTranslator
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)


class ReferenceInMemoryTranslator(IReferenceTranslator):
    @classmethod
    def get_reference(cls, entity_id: PropositionIdentity) -> str:
        proposition = PropositionInMemoryRepository.get(entity_id)
        formation = FormationGeneraleInMemoryTranslator.get_dto(
            proposition.formation_id.sigle,
            proposition.formation_id.annee,
        )

        return formater_reference(
            reference=proposition.reference,
            nom_campus_inscription=formation.campus_inscription.nom,
            sigle_entite_gestion=formation.sigle_entite_gestion,
            annee=formation.annee,
        )
