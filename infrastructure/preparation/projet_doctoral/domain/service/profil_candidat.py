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
from admission.ddd.preparation.projet_doctoral.dtos import IdentificationDTO
from base.models.person import Person


class ProfilCandidatTranslator(IProfilCandidatTranslator):
    @classmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':
        person = Person.objects.select_related(
            'country_of_citizenship',
        ).get(global_id=matricule)

        return IdentificationDTO(
            matricule=matricule,
            nom=person.last_name,
            prenom=person.first_name,
            date_naissance=person.birth_date,
            annee_naissance=person.birth_year,
            pays_nationalite=person.country_of_citizenship.iso_code if person.country_of_citizenship else None,
            langue_contact=person.language,
            sexe=person.sex,
            genre=person.gender,
            photo_identite=person.id_photo,
            carte_identite=person.id_card,
            passeport=person.passport,
            numero_registre_national_belge=person.national_number,
            numero_carte_identite=person.id_card_number,
            numero_passeport=person.passport_number,
            date_expiration_passeport=person.passport_expiration_date,
        )

    @classmethod
    def get_coordonnees(cls, matricule: str) -> 'CoordonneesDTO':
        pass

    @classmethod
    def get_curriculum(cls, matricule: str) -> 'CurriculumDTO':
        pass
