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
from django.db.models import DateField, Q
from django.db.models.expressions import F, RawSQL
from django.db.models.functions import Cast

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.models.base import BaseAdmission


def initialize_requested_documents_deadline(model_class=BaseAdmission):
    """
    Previously, the deadline date of the document request was stored at document level
    (admission.requested_documents.doc_1.deadline_at). We want store it at admission level (admission.last_request_document_deadline).
    :param model_class:
    :return:
    """
    qs = (
        model_class.objects.filter(
            Q(
                Q(
                    generaleducationadmission__status__in=[
                        ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
                        ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
                    ]
                )
                | Q(continuingeducationadmission__status=ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name)
                | Q(
                    doctorateadmission__status__in=[
                        ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name,
                        ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name,
                    ]
                )
            )
        )
        .annotate(
            # Get the deadline from one of the requested and last updated documents
            last_request_document_deadline=Cast(
                RawSQL(
                    """
                    SELECT value->>'deadline_at'
                    FROM jsonb_each(requested_documents) as entry
                    WHERE value->>'status' = %s
                    ORDER BY (value->>'last_action_at')::timestamp DESC
                    LIMIT 1
                    """,
                    params=[
                        StatutEmplacementDocument.RECLAME.name,
                    ],
                ),
                output_field=DateField(),
            ),
        )
        .update(
            requested_documents_deadline=F('last_request_document_deadline'),
        )
    )
