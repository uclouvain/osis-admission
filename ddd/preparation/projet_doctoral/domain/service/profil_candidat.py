# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.preparation.projet_doctoral.domain.model._candidat_adresse import CandidatAdresse
from admission.ddd.preparation.projet_doctoral.domain.model._candidat_signaletique import CandidatSignaletique
from admission.ddd.preparation.projet_doctoral.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.preparation.projet_doctoral.domain.validator.validator_by_business_action import (
    IdentificationValidatorList,
    CoordonneesValidatorList,
    LanguesConnuesValidatorList
)
from osis_common.ddd import interface


class ProfilCandidat(interface.DomainService):
    @classmethod
    def verifier_identification(cls, matricule: str, profil_candidat_translator: 'IProfilCandidatTranslator') -> None:
        identification = profil_candidat_translator.get_identification(matricule)
        IdentificationValidatorList(
            identite_signaletique=CandidatSignaletique(
                annee_naissance=identification.annee_naissance,
                date_naissance=identification.date_naissance,
                pays_nationalite=identification.pays_nationalite,
                photo_identite=identification.photo_identite,
                prenom=identification.prenom,
                langue_contact=identification.langue_contact,
                sexe=identification.sexe,
                nom=identification.nom,
                genre=identification.genre,
            ),
            date_naissance=identification.date_naissance,
            annee_naissance=identification.annee_naissance,
            numero_registre_national_belge=identification.numero_registre_national_belge,
            numero_carte_identite=identification.numero_carte_identite,
            carte_identite=identification.carte_identite,
            numero_passeport=identification.numero_passeport,
            passeport=identification.passeport,
            date_expiration_passeport=identification.date_expiration_passeport,
        ).validate()

    @classmethod
    def verifier_coordonnees(cls, matricule: str, profil_candidat_translator: 'IProfilCandidatTranslator') -> None:
        coordonnees = profil_candidat_translator.get_coordonnees(matricule)

        CoordonneesValidatorList(
            domicile_legal=CandidatAdresse(
                code_postal=coordonnees.domicile_legal.code_postal,
                ville=coordonnees.domicile_legal.ville,
                pays=coordonnees.domicile_legal.pays,
                rue=coordonnees.domicile_legal.rue,
            ) if coordonnees.domicile_legal else None,
            adresse_correspondance=CandidatAdresse(
                code_postal=coordonnees.adresse_correspondance.code_postal,
                ville=coordonnees.adresse_correspondance.ville,
                pays=coordonnees.adresse_correspondance.pays,
                rue=coordonnees.adresse_correspondance.rue,
            ) if coordonnees.adresse_correspondance else None
        ).validate()

    @classmethod
    def verifier_langues_connues(cls, matricule: str, profil_candidat_translator: 'IProfilCandidatTranslator') -> None:
        langues_connues = profil_candidat_translator.get_langues_connues(matricule)

        LanguesConnuesValidatorList(
            nb_langues_connues_requises=langues_connues.nb_langues_connues_requises,
            langues_requises=profil_candidat_translator.CODES_LANGUES_CONNUES_REQUISES,
        ).validate()

    @classmethod
    def verifier_curriculum(cls, profil_candidat_translator: 'IProfilCandidatTranslator') -> None:
        raise NotImplementedError
