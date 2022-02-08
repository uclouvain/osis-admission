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
from admission.ddd.preparation.projet_doctoral.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import CandidatNonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import IdentificationDTO, CountryDTO, AcademicYearDTO
from base.tests.factories.person import PersonFactory


# @dataclass
# class ProfilCandidat:
#     nom: str
#     prenom: str
#     prenom_d_usage: str
#     autres_prenoms: str
#     date_naissance: str
#     annee_naissance: int
#     pays_naissance: str
#     lieu_naissance: str
#     pays_nationalite: str
#     langue_contact: str
#     sexe: str
#     genre: str
#     etat_civil: str
#     photo_identite: List[str]
#
#     # Pièces d'identité
#     carte_identite: List[str]
#     passeport: List[str]
#     numero_registre_national_belge: str
#     numero_carte_identite: str
#     numero_passeport: str
#     date_expiration_passeport: str
#
#     # Déjà inscrit précédemment ?
#     annee_derniere_inscription: str


class ProfilCandidatInMemoryTranslator(IProfilCandidatTranslator):
    profil_candidats = [
        PersonFactory(global_id='user1'),
        PersonFactory(global_id='user2'),
        PersonFactory(global_id='user3'),
    ]

    @classmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':
        try:
            candidate = next(c for c in cls.profil_candidats if c.global_id == matricule)
            return IdentificationDTO(
                matricule=matricule,
                nom=candidate.person.last_name,
                prenom=candidate.person.first_name,
                date_naissance=candidate.person.birth_date,
                annee_naissance=candidate.person.birth_year,
                pays_nationalite=CountryDTO(
                    id=candidate.person.country_of_citizenship_id,
                    iso_code=candidate.person.country_of_citizenship.iso_code,
                ),
                langue_contact=candidate.person.language,  # +
                sexe=candidate.person.sex,
                genre=candidate.person.genre,
                photo_identite=candidate.person.id_photo,
                carte_identite=candidate.person.id_card,
                passeport=candidate.person.passport,
                numero_registre_national_belge=candidate.person.national_number,
                numero_carte_identite=candidate.person.id_card_number,
                numero_passeport=candidate.person.passport_number,
                date_expiration_passeport=candidate.person.passport_expiration_date,
                annee_derniere_inscription=AcademicYearDTO(
                    id=candidate.person.last_registration_year_id,
                    year=candidate.person.last_registration_year.year,
                ),
            )
        except StopIteration:  # pragma: no cover
            raise CandidatNonTrouveException

    @classmethod
    def get_coordonnees(cls, matricule: str) -> 'CoordonneesDTO':
        pass

    @classmethod
    def get_curriculum(cls, matricule: str) -> 'CurriculumDTO':
        pass
