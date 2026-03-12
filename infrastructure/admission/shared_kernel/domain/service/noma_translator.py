# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.shared_kernel.domain.service.i_noma_translator import INomasTranslator
from ddd.logic.shared_kernel.signaletique_etudiant.commands import RechercherSignaletiqueEtudiantQuery
from ddd.logic.shared_kernel.signaletique_etudiant.dto.signaletique_etudiant import SignaletiqueEtudiantDTO

class NomasTranslator(INomasTranslator):
    @classmethod
    def recuperer(
        cls,
        matricule_candidat: str,
    ) -> list[str]:
        from infrastructure.messages_bus import message_bus_instance

        students: set[SignaletiqueEtudiantDTO] = message_bus_instance.invoke(
            RechercherSignaletiqueEtudiantQuery(matricule_fgs=matricule_candidat),
        )

        return [student.noma for student in students]
