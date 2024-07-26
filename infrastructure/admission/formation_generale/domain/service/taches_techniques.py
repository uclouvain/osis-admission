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

from admission.models import GeneralEducationAdmission
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutChecklist
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import StatutChecklist
from admission.ddd.admission.formation_generale.domain.service.i_taches_techniques import ITachesTechniques


class TachesTechniques(ITachesTechniques):
    @classmethod
    def annuler_paiement_initial_frais_dossier(
        cls,
        proposition: Proposition,
        statut_checklist_frais_dossier_avant_modification: StatutChecklist,
    ):
        if (
            statut_checklist_frais_dossier_avant_modification.statut == ChoixStatutChecklist.GEST_BLOCAGE
            and statut_checklist_frais_dossier_avant_modification.extra.get('initial') == '1'
        ):
            admission = GeneralEducationAdmission.objects.get(uuid=proposition.entity_id.uuid)

            from admission.tasks.merge_admission_documents import base_education_admission_document_merging

            # Merge the documents
            base_education_admission_document_merging(admission=admission)

            # Generate and save the PDF recap if not already done
            if admission.pdf_recap:
                return

            from admission.exports.admission_recap.admission_recap import admission_pdf_recap

            token = admission_pdf_recap(admission=admission, language=admission.candidate.language)

            admission.pdf_recap = [token]
            admission.save(update_fields=['pdf_recap'])
