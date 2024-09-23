# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratDTO
from admission.ddd.admission.doctorat.preparation.test.factory.doctorat import (
    DoctoratCDEFactory,
    DoctoratCDSCFactory,
    DoctoratCDSSDPFactory,
    DoctoratCLSMFactory,
    _DoctoratDTOFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.doctorat import DoctoratEtendu
from admission.ddd.admission.test.factory.formation import CampusFactory


class DoctoratInMemoryTranslator(IDoctoratTranslator):
    doctorats = [
        DoctoratCDEFactory(
            entity_id__sigle='ECGE3DP',
            entity_id__annee=2020,
            campus='Louvain-la-Neuve',
            campus_inscription='Louvain-la-Neuve',
            code_secteur='SSH',
            intitule='Doctorat en sciences économiques et de gestion',
            intitule_secteur='Secteur des sciences humaines',
        ),
        DoctoratCLSMFactory(
            entity_id__sigle='ECGM3DP',
            entity_id__annee=2020,
            campus='Mons',
        ),
        DoctoratCDSCFactory(
            entity_id__sigle='AGRO3DP',
            entity_id__annee=2020,
            campus='Louvain-la-Neuve',
        ),
        DoctoratCDSCFactory(
            entity_id__sigle='SC3DP',
            entity_id__annee=2020,
            campus='Louvain-la-Neuve',
            campus_inscription='Louvain-la-Neuve',
            code_secteur='SST',
            intitule='Doctorat en sciences',
            intitule_secteur='Secteur des sciences et technologies',
        ),
        DoctoratCDSSDPFactory(
            entity_id__sigle='ESP3DP',
            entity_id__annee=2020,
            campus='Mons',
            campus_inscription='Mons',
            code_secteur='SSS',
            intitule='Doctorat en sciences de la santé publique',
            intitule_secteur='Secteur des sciences de la santé',
        ),
        DoctoratCDSSDPFactory(
            entity_id__sigle='AGRO3DP',
            entity_id__annee=2022,
            campus='Charleroi',
        ),
    ]
    sector_doctorates_mapping = {
        "SST": ['AGRO3DP', 'SC3DP'],
        "SSH": ['ECGE3DP', 'ECGM3DP'],
        "SSS": ['ESP3DP'],
    }

    secteurs_par_doctorat = {
        doctorate: sector for sector, doctorates in sector_doctorates_mapping.items() for doctorate in doctorates
    }

    intitules_secteurs = {
        'SST': 'Secteur des sciences et technologies',
        'SSH': 'Secteur des sciences humaines',
        'SSS': 'Secteur des sciences de la santé',
    }

    @classmethod
    def get(cls, sigle: str, annee: int) -> 'DoctoratEtendu':
        try:
            return next(doc for doc in cls.doctorats if doc.entity_id.sigle == sigle and doc.entity_id.annee == annee)
        except StopIteration:
            raise DoctoratNonTrouveException()

    @classmethod
    def get_dto(cls, sigle: str, annee: int) -> DoctoratDTO:  # pragma: no cover
        doctorate = cls.get(sigle, annee)
        return _DoctoratDTOFactory(
            sigle=doctorate.entity_id.sigle,
            annee=doctorate.entity_id.annee,
            sigle_entite_gestion=doctorate.entite_ucl_id.code,
            intitule=doctorate.intitule,
            intitule_en=doctorate.intitule,
            intitule_fr=doctorate.intitule,
            campus=CampusFactory(nom=doctorate.campus),
            type=doctorate.type,
            campus_inscription=CampusFactory(nom=doctorate.campus_inscription),
        )

    @classmethod
    def search(
        cls,
        sigle_secteur_entite_gestion: str,
        annee: Optional[int] = None,
        campus: Optional[str] = '',
        terme_de_recherche: Optional[str] = '',
    ) -> List['DoctoratDTO']:
        doctorates = cls.sector_doctorates_mapping.get(sigle_secteur_entite_gestion, [])
        return [
            _DoctoratDTOFactory(
                sigle=doc.entity_id.sigle,
                annee=doc.entity_id.annee,
                sigle_entite_gestion=doc.entite_ucl_id.code,
            )
            for doc in cls.doctorats
            if doc.entity_id.sigle in doctorates
            and doc.entity_id.annee == annee
            and (not campus or doc.campus == campus)
            and (terme_de_recherche in doc.intitule or terme_de_recherche in doc.sigle)
        ]

    @classmethod
    def verifier_existence(cls, sigle: str, annee: int) -> bool:  # pragma: no cover
        return any(True for doc in cls.doctorats if doc.entity_id.sigle == sigle and doc.entity_id.annee == annee)
