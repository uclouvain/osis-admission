# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
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
from typing import List

from admission.ddd.preparation.projet_doctoral.domain.model.doctorat import Doctorat
from admission.ddd.preparation.projet_doctoral.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import DoctoratDTO
from admission.ddd.preparation.projet_doctoral.test.factory.doctorat import (
    DoctoratCDEFactory,
    DoctoratCDSCFactory,
    DoctoratCDSSDPFactory,
    _DoctoratDTOFactory,
)


class DoctoratInMemoryTranslator(IDoctoratTranslator):
    doctorats = [
        DoctoratCDEFactory(
            entity_id__sigle='ECGE3DP',
            entity_id__annee=2020,
            entite_ucl_id__code="CDE",
        ),
        DoctoratCDSCFactory(
            entity_id__sigle='AGRO3DP',
            entity_id__annee=2020,
        ),
        DoctoratCDSCFactory(
            entity_id__sigle='SC3DP',
            entity_id__annee=2020,
        ),
        DoctoratCDSSDPFactory(
            entity_id__sigle='ESP3DP',
            entity_id__annee=2020,
        ),
    ]
    sector_doctorates_mapping = {
        "SST": ['AGRO3DP', 'SC3DP'],
        "SSH": ['ECGE3DP'],
        "SSS": ['ESP3DP'],
    }

    @classmethod
    def get(cls, sigle: str, annee: int) -> 'Doctorat':
        try:
            return next(doc for doc in cls.doctorats if doc.entity_id.sigle == sigle and doc.entity_id.annee == annee)
        except StopIteration:
            raise DoctoratNonTrouveException()

    @classmethod
    def get_dto(cls, sigle: str, annee: int) -> DoctoratDTO:
        doctorate = cls.get(sigle, annee)
        return _DoctoratDTOFactory(
            sigle=doctorate.entity_id.sigle,
            annee=doctorate.entity_id.annee,
            sigle_entite_gestion=doctorate.entite_ucl_id.code,
        )

    @classmethod
    def search(cls, sigle_secteur_entite_gestion: str, annee: int) -> List['DoctoratDTO']:
        doctorates = cls.sector_doctorates_mapping.get(sigle_secteur_entite_gestion, [])
        return [_DoctoratDTOFactory(
            sigle=doc.entity_id.sigle,
            annee=doc.entity_id.annee,
            sigle_entite_gestion=doc.entite_ucl_id.code,
        ) for doc in cls.doctorats if doc.entity_id.sigle in doctorates and doc.entity_id.annee == annee]
