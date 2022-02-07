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
from admission.auth.roles.candidate import Candidate
from admission.ddd.preparation.projet_doctoral.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.preparation.projet_doctoral.dtos import IdentificationDTO, AcademicYearDTO, CountryDTO


class ProfilCandidatTranslator(IProfilCandidatTranslator):
    @classmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':
        candidat_role = Candidate.objects.select_related(
            'person',
            'person__birth_country',
            'person__country_of_citizenship',
            'person__last_registration_year',
        ).get(person__global_id=matricule)

        return IdentificationDTO(
            matricule=matricule,
            nom=candidat_role.person.last_name,
            prenom=candidat_role.person.first_name,
            prenom_d_usage=candidat_role.person.first_name_in_use,
            autres_prenoms=candidat_role.person.middle_name,
            date_naissance=candidat_role.person.birth_date,
            annee_naissance=candidat_role.person.birth_year,
            pays_naissance=CountryDTO(
                id=candidat_role.person.birth_country_id,
                iso_code=candidat_role.person.birth_country.iso_code,
            ),
            lieu_naissance=candidat_role.person.birth_place,
            pays_nationalite=CountryDTO(
                id=candidat_role.person.country_of_citizenship_id,
                iso_code=candidat_role.person.country_of_citizenship.iso_code,
            ),
            langue_contact=candidat_role.person.language,  # +
            sexe=candidat_role.person.sex,
            genre=candidat_role.person.genre,
            etat_civil=candidat_role.person.civil_state,
            photo_identite=candidat_role.person.id_photo,
            carte_identite=candidat_role.person.id_card,
            passeport=candidat_role.person.passport,
            numero_registre_national_belge=candidat_role.person.national_number,
            numero_carte_identite=candidat_role.person.id_card_number,
            numero_passeport=candidat_role.person.passport_number,
            date_expiration_passeport=candidat_role.person.passport_expiration_date,
            annee_derniere_inscription=AcademicYearDTO(
                id=candidat_role.person.last_registration_year_id,
                year=candidat_role.person.last_registration_year.year,
            )
    )
