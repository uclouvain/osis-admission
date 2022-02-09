# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from dataclasses import dataclass
from typing import List, Optional

from admission.ddd.preparation.projet_doctoral.domain.model._candidat import CandidatIdentity
from admission.ddd.preparation.projet_doctoral.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import CandidatNonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import IdentificationDTO, CountryDTO


@dataclass
class ProfilCandidat:
    global_id: CandidatIdentity
    nom: Optional[str]
    prenom: Optional[str]
    prenom_d_usage: Optional[str]
    autres_prenoms: Optional[str]
    date_naissance: Optional[datetime.date]
    annee_naissance: Optional[int]
    lieu_naissance: Optional[str]
    pays_nationalite: Optional[CountryDTO]
    langue_contact: Optional[str]
    sexe: Optional[str]
    genre: Optional[str]
    photo_identite: List[str]

    # Pièces d'identité
    carte_identite: List[str]
    passeport: List[str]
    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    numero_passeport: Optional[str]
    date_expiration_passeport: Optional[datetime.date]


class ProfilCandidatInMemoryTranslator(IProfilCandidatTranslator):
    profil_candidats = [
        ProfilCandidat(
            global_id=CandidatIdentity(
                matricule='user1',
            ),
            nom='Doe',
            prenom='John',
            prenom_d_usage='Jerry',
            autres_prenoms='James',
            date_naissance=datetime.date(1990, 1, 1),
            annee_naissance=1990,
            lieu_naissance='Louvain-La-Neuve',
            pays_nationalite=CountryDTO(
                iso_code='BE',
                id=1,
            ),
            langue_contact='fr-be',
            sexe='M',
            genre='M',
            photo_identite=['uuid11'],
            carte_identite=['uuid12'],
            passeport=['uuid13'],
            numero_registre_national_belge='1001',
            numero_carte_identite='1002',
            numero_passeport='1003',
            date_expiration_passeport=datetime.date(2022, 2, 10),
        ),
        ProfilCandidat(
            global_id=CandidatIdentity(
                matricule='user2',
            ),
            nom='Dean',
            prenom='Jack',
            prenom_d_usage='Jared',
            autres_prenoms='Jim',
            date_naissance=datetime.date(1991, 1, 1),
            annee_naissance=1991,
            lieu_naissance='Louvain-La-Neuve',
            pays_nationalite=CountryDTO(
                iso_code='BE',
                id=1,
            ),
            langue_contact='fr-be',
            sexe='M',
            genre='M',
            photo_identite=['uuid21'],
            carte_identite=['uuid22'],
            passeport=['uuid23'],
            numero_registre_national_belge='2001',
            numero_carte_identite='2002',
            numero_passeport='2003',
            date_expiration_passeport=datetime.date(2023, 2, 10),
        ),
    ]

    @classmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':
        try:
            candidate = next(c for c in cls.profil_candidats if c.global_id.matricule == matricule)
            return IdentificationDTO(
                matricule=matricule,
                nom=candidate.nom,
                prenom=candidate.prenom,
                date_naissance=candidate.date_naissance,
                annee_naissance=candidate.annee_naissance,
                pays_nationalite=CountryDTO(
                    id=candidate.pays_nationalite.id,
                    iso_code=candidate.pays_nationalite.iso_code,
                )
                if candidate.pays_nationalite
                else None,
                langue_contact=candidate.langue_contact,
                sexe=candidate.sexe,
                genre=candidate.genre,
                photo_identite=candidate.photo_identite,
                carte_identite=candidate.carte_identite,
                passeport=candidate.passeport,
                numero_registre_national_belge=candidate.numero_registre_national_belge,
                numero_carte_identite=candidate.numero_carte_identite,
                numero_passeport=candidate.numero_passeport,
                date_expiration_passeport=candidate.date_expiration_passeport,
            )
        except StopIteration:  # pragma: no cover
            raise CandidatNonTrouveException

    @classmethod
    def get_coordonnees(cls, matricule: str) -> 'CoordonneesDTO':
        pass

    @classmethod
    def get_curriculum(cls, matricule: str) -> 'CurriculumDTO':
        pass
