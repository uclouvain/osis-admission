# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, List

from dal_select2.views import Select2ListView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from admission.constants import CONTEXT_CONTINUING, CONTEXT_DOCTORATE, CONTEXT_GENERAL
from admission.ddd.admission.doctorat.preparation import (
    commands as doctorate_education_commands,
)
from admission.ddd.admission.formation_continue import (
    commands as continuing_education_commands,
)
from admission.ddd.admission.formation_generale import (
    commands as general_education_commands,
)
from admission.ddd.admission.shared_kernel.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.shared_kernel.enums.emplacement_document import (
    DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION,
    EMPLACEMENTS_DOCUMENTS_INTERNES,
    IdentifiantBaseEmplacementDocument,
)
from admission.models.base import BaseAdmission
from infrastructure.messages_bus import message_bus_instance

__namespace__ = False


__all__ = [
    'DocumentTypesForSwappingAutocomplete',
]


class DocumentTypesForSwappingAutocomplete(Select2ListView):
    urlpatterns = 'document-types-swap'
    retrieve_documents_command = {
        CONTEXT_GENERAL: general_education_commands.RecupererDocumentsPropositionQuery,
        CONTEXT_CONTINUING: continuing_education_commands.RecupererDocumentsPropositionQuery,
        CONTEXT_DOCTORATE: doctorate_education_commands.RecupererDocumentsPropositionQuery,
    }
    category_icons = {
        IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name: ' <i class="fa-solid fa-dice"></i>',
    }

    def get(self, request, *args, **kwargs):
        document_identifier = self.forwarded.get('document_identifier')
        admission_uuid = self.forwarded.get('admission_uuid')
        admission = get_object_or_404(BaseAdmission, uuid=admission_uuid)
        admission_context = admission.get_admission_context()

        documents: List[EmplacementDocumentDTO] = (
            message_bus_instance.invoke(
                self.retrieve_documents_command[admission_context](
                    uuid_proposition=admission_uuid,
                )
            )
            if admission_context in self.retrieve_documents_command
            else []
        )

        documents_by_category: Dict[str, List[EmplacementDocumentDTO]] = {}
        category_names: Dict[str, str] = {}
        search_term = self.q.lower()

        for document in documents:
            if search_term and search_term not in document.libelle.lower():
                continue

            if document.onglet not in category_names:
                category_names[document.onglet] = '{category_name}{category_icon}'.format(
                    category_name=document.nom_onglet,
                    category_icon=self.category_icons.get(document.onglet, ''),
                )

            if (
                document.type not in EMPLACEMENTS_DOCUMENTS_INTERNES
                and document.identifiant not in DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION
            ):
                documents_by_category.setdefault(document.onglet, []).append(document)

        results = [
            {
                'text': category_names.get(category, ''),
                'children': [
                    {
                        'id': document.identifiant,
                        'text': (
                            '<i class="fa-solid fa-{has_document_icon}"></i>{free_document_icon} {name}'.format(
                                has_document_icon='paperclip' if document.document_uuids else 'link-slash',
                                free_document_icon=(
                                    ' <i class="fa-solid fa-dice free-document"></i>'
                                    if document.est_emplacement_document_libre
                                    else ''
                                ),
                                name=document.libelle,
                            )
                        ),
                        'disabled': document.identifiant == document_identifier,
                    }
                    for document in category_documents
                ],
            }
            for category, category_documents in documents_by_category.items()
        ]
        return JsonResponse(
            {
                'pagination': {'more': False},
                'results': results,
            },
        )
