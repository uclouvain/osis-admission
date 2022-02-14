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
from itertools import chain

from admission.ddd.preparation.projet_doctoral.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.preparation.projet_doctoral.dtos import (
    IdentificationDTO,
    CoordonneesDTO,
    AdressePersonnelleDTO,
    LanguesConnuesDTO,
    CurriculumDTO,
)
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from osis_profile.models import CurriculumYear, BelgianHighSchoolDiploma, ForeignHighSchoolDiploma
from osis_profile.models.education import LanguageKnowledge


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
        # TODO Use in_bulk() in Django 3.2
        adresses = {
            a.label: a
            for a in PersonAddress.objects.select_related('country').filter(
                person__global_id=matricule,
                label__in=[PersonAddressType.CONTACT.name, PersonAddressType.RESIDENTIAL.name],
            )
        }
        domicile_legal = adresses.get(PersonAddressType.RESIDENTIAL.name)
        adresse_correspondance = adresses.get(PersonAddressType.CONTACT.name)

        return CoordonneesDTO(
            domicile_legal=AdressePersonnelleDTO(
                rue=domicile_legal.street,
                code_postal=domicile_legal.postal_code,
                ville=domicile_legal.city,
                pays=domicile_legal.country.iso_code if domicile_legal.country else None,
            ) if domicile_legal else None,
            adresse_correspondance=AdressePersonnelleDTO(
                rue=adresse_correspondance.street,
                code_postal=adresse_correspondance.postal_code,
                ville=adresse_correspondance.city,
                pays=adresse_correspondance.country.iso_code if adresse_correspondance.country else None,
            ) if adresse_correspondance else None,
        )

    @classmethod
    def get_langues_connues(cls, matricule: str) -> 'LanguesConnuesDTO':
        nb_langues_connues_requises = (
            LanguageKnowledge.objects.filter(
                person__global_id=matricule,
                language__code__in=cls.CODES_LANGUES_CONNUES_REQUISES,
            )
            .limit(len(cls.CODES_LANGUES_CONNUES_REQUISES))
            .count()
        )

        return LanguesConnuesDTO(
            nb_langues_connues_requises=nb_langues_connues_requises,
        )

    @classmethod
    def get_curriculum(cls, matricule: str) -> 'CurriculumDTO':
        person = Person.objects.select_related(
            'last_registration_year',
            'belgianhighschooldiploma__academic_graduation_year',
            'foreignhighschooldiploma__academic_graduation_year',
        ).get(global_id=matricule)

        annees_curriculum = CurriculumYear.objects.select_related('academic_year').filter(
            person__global_id=matricule,
        ).limit(cls.NB_MAX_ANNEES_CV_REQUISES)

        annee_diplome_etudes_secondaires_belges, annee_diplome_etudes_secondaires_etrangeres = None

        if person.belgianhighschooldiploma:
            annee_diplome_etudes_secondaires_belges = person.belgianhighschooldiploma.academic_graduation_year.year
        if person.foreignhighschooldiploma:
            annee_diplome_etudes_secondaires_etrangeres = person.foreignhighschooldiploma.academic_graduation_year.year

        return CurriculumDTO(
            annees=set(academic_year.year for academic_year in annees_curriculum),
            annee_diplome_etudes_secondaires_belges=annee_diplome_etudes_secondaires_belges,
            annee_diplome_etudes_secondaires_etrangeres=annee_diplome_etudes_secondaires_etrangeres,
            annee_derniere_inscription_ucl=person.last_registration_year.year if person.last_registration_year else None,
            fichier_pdf=person.curriculum,
        )
