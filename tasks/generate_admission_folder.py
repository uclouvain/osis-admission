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
from django.utils.translation import gettext as _

from admission.models import (
    AdmissionTask,
    GeneralEducationAdmission,
    ContinuingEducationAdmission,
    DoctorateAdmission,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums.emplacement_document import TypeEmplacementDocument
from admission.ddd.admission.formation_continue import commands as continuing_commands
from admission.ddd.admission.doctorat.preparation import commands as doctorate_commands
from admission.ddd.admission.formation_generale import commands as general_commands
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.exports.admission_recap.admission_recap import admission_pdf_recap


__all__ = [
    'continuing_education_admission_analysis_folder_from_task',
    'general_education_admission_analysis_folder_from_task',
]


def general_education_admission_analysis_folder_from_task(task_uuid: str):
    """Generates the analysis folder for a general education admission and save it."""
    task = AdmissionTask.objects.select_related('admission__candidate', 'admission__generaleducationadmission').get(
        task__uuid=task_uuid
    )

    # Generate the analysis folder
    token = admission_pdf_recap(task.admission, task.admission.candidate.language, GeneralEducationAdmission)

    # Save the analysis folder in the admission
    from infrastructure.messages_bus import message_bus_instance

    message_bus_instance.invoke(
        general_commands.InitialiserEmplacementDocumentLibreNonReclamableCommand(
            uuid_proposition=task.admission.uuid,
            auteur=task.admission.candidate.global_id,
            uuid_document=token,
            type_emplacement={
                ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name: TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
                ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name: TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
            }.get(task.admission.generaleducationadmission.status, TypeEmplacementDocument.LIBRE_INTERNE_SIC.name),
            libelle=_('Analysis file generated when the documents requested from the candidate are received'),
        )
    )


def continuing_education_admission_analysis_folder_from_task(task_uuid: str):
    """Generates the analysis folder for a continuing education admission and save it."""
    task = AdmissionTask.objects.select_related('admission__candidate').get(task__uuid=task_uuid)

    # Generate the analysis folder
    token = admission_pdf_recap(task.admission, task.admission.candidate.language, ContinuingEducationAdmission)

    # Save the analysis folder in the admission
    from infrastructure.messages_bus import message_bus_instance

    message_bus_instance.invoke(
        continuing_commands.InitialiserEmplacementDocumentLibreNonReclamableCommand(
            uuid_proposition=task.admission.uuid,
            auteur=task.admission.candidate.global_id,
            uuid_document=token,
            type_emplacement=TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
            libelle=_('Analysis file generated when the documents requested from the candidate are received'),
        )
    )


def doctorate_education_admission_analysis_folder_from_task(task_uuid: str):
    """Generates the analysis folder for a general education admission and save it."""
    task = AdmissionTask.objects.select_related('admission__candidate', 'admission__doctorateadmission').get(
        task__uuid=task_uuid,
    )

    # Generate the analysis folder
    token = admission_pdf_recap(task.admission, task.admission.candidate.language)

    # Save the analysis folder in the admission
    from infrastructure.messages_bus import message_bus_instance

    message_bus_instance.invoke(
        doctorate_commands.InitialiserEmplacementDocumentLibreNonReclamableCommand(
            uuid_proposition=task.admission.uuid,
            auteur=task.admission.candidate.global_id,
            uuid_document=token,
            type_emplacement={
                ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC.name: TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
                ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name: TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
            }.get(task.admission.doctorateadmission.status, TypeEmplacementDocument.LIBRE_INTERNE_SIC.name),
            libelle=_('Analysis file generated when the documents requested from the candidate are received'),
        )
    )
