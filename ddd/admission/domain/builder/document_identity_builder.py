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

from admission.ddd.admission.domain.model.document import DocumentIdentity
from admission.ddd.admission.enums.document import TypeDocument
from osis_common.ddd import interface


class DocumentIdentityBuilder(interface.EntityIdentityBuilder):
    @classmethod
    def build(
        cls,
        type_document: TypeDocument,
        identifiant_document: str = '',
        token_document: str = '',
        identifiant_question_specifique: str = '',
    ) -> DocumentIdentity:
        return DocumentIdentity(
            identifiant={
                TypeDocument.INTERNE_FAC: token_document,
                TypeDocument.INTERNE_SIC: token_document,
                TypeDocument.NON_LIBRE: identifiant_document,
                TypeDocument.CANDIDAT_FAC: identifiant_question_specifique or token_document,
                TypeDocument.CANDIDAT_SIC: identifiant_question_specifique or token_document,
                TypeDocument.SYSTEME: identifiant_document,
            }[type_document]
        )
