# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, List, Optional, Union

import attr
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition as PropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.validator.exceptions import ElementsConfirmationNonConcordants
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition as PropositionContinue
from admission.ddd.admission.formation_continue.domain.service.i_formation import IFormationContinueTranslator
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGenerale
from admission.ddd.admission.formation_generale.domain.service.i_formation import IFormationGeneraleTranslator
from base.models.enums.academic_calendar_type import AcademicCalendarTypes, AcademicCalendarTypes as Pool
from base.models.enums.education_group_types import TrainingType
from osis_common.ddd import interface

IFormationTranlator = Union[IFormationContinueTranslator, IFormationGeneraleTranslator, IDoctoratTranslator]


@attr.dataclass
class ElementConfirmation:
    nom: str
    texte: str
    reponses: Optional[List[str]] = None
    titre: str = ""
    type: str = 'checkbox'


class IElementsConfirmation(interface.DomainService):
    HORS_DELAI = _(
        'In accordance with the registration calendar '
        '<a href="https://uclouvain.be/en/study/inscriptions/calendrier-inscriptions.html" target="_blank">'
        'www.uclouvain.be/enrolment-calendar</a>, I confirm that I am applying for the academic year %(year)s.'
    )
    REGLEMENT_GENERAL = _(
        'In accordance with the information on the link <a target="_blank" href="'
        'https://uclouvain.be/en/study/inscriptions/reglementations.html">'
        'www.uclouvain.be/regulation-enrolment</a>, I declare that I have read the university regulations '
        'and accept their terms.'
    )
    PROTECTION_DONNEES = _(
        'In accordance with the information on the link <a target="_blank" href="'
        'https://uclouvain.be/en/study/inscriptions/vie-privee.html">www.uclouvain.be/privacy-enrolment'
        '</a>, I declare that I have read the data protection policy of UCLouvain and I accept its terms.'
    )
    PROFESSIONS_REGLEMENTEES = _(
        'In accordance with the information on the link, <a target="_blank" href="'
        'https://uclouvain.be/en/study/inscriptions/acces-aux-professions-reglementees.html">'
        'www.uclouvain.be/regulated-professions</a>, I declare that I have received, if these studies '
        'concern me, information on the conditions of access to these studies or of access to the '
        'continuation of these studies and on the particular rules or restrictions of accreditation or '
        'professional establishment to which the professional or associate title is subject, and I accept '
        'the terms thereof.'
    )
    FRAIS_DOSSIER = _(
        'I am aware that as a non-EU, non-assimilated student, I am required to pay a &euro;200 '
        'application fee via the online payment system. The application fee must be received by '
        'UCLouvain <strong>within 15 calendar days</strong>. If not, my application will be closed. '
        'For more information: '
        '<a href="https://uclouvain.be/en/study/inscriptions/tuition-fees-non-eu-students.html" '
        'target="_blank">www.uclouvain.be/application-fees</a>.'
    )
    CONVENTION_CADRE_STAGE = _(
        'I have taken note of the latest version of the Internship framework agreement between '
        'UCLouvain and the Host Hospitals established within the framework of bachelor\'s or '
        'master\'s training in medicine organised by UCLouvain with a view to acquiring the '
        'corresponding teaching units, and I undertake to respect the terms thereof: '
        '<a href="https://cdn.uclouvain.be/groups/cms-editors-mede/ConventionStageMed.pdf" '
        'target="_blank">https://cdn.uclouvain.be/groups/cms-editors-mede/ConventionStageMed.pdf</a>'
    )
    COMMUNICATION_HOPITAUX = _(
        'I authorise the Faculty of Medicine and Dentistry of UCLouvain to provide my personal details '
        '(surname(s), first name(s), NOMA, date of birth, place of birth, address) to the '
        'Host Hospitals with a view to establishing the various accesses that will be necessary '
        'for me in the context of my internship, and this in compliance with the General Data '
        'Protection Regulation (GDPR) and the law of 30 July 2018 on the protection of individuals '
        'with regard to the processing of personal data. My data is kept for the time necessary for '
        'the proper execution of the internship and is never passed on to parties other than those '
        'mentioned above. Appropriate technical and organisational measures are put in place to '
        'ensure an adequate level of protection of this data.'
    )
    DOCUMENTS_ETUDES_CONTINGENTEES = _(
        'I am aware that no additional documents specific to quota studies can be added after my online '
        'application has been confirmed.'
    )
    COMMUNICATION_ECOLE_SECONDAIRE = _(
        'UCLouvain to transmit, to the secondary school in which I obtained my CESS, the information '
        'relating to the successful completion of the 1st annual bachelor\'s degree and any academic '
        'degree obtained with the possible mention.'
    )
    JUSTIFICATIFS = _(
        'I undertake to send any supporting documents requested by the Enrolment Service <strong>within 15 calendar '
        'days</strong>. If I fail to do so, I take note and accept that my application will be closed.'
    )
    DECLARATION_SUR_LHONNEUR = _(
        '<ul><li>the information I have provided in this application is accurate and complete</li>'
        '<li>I have uploaded all relevant documents confirming the information provided</li>'
        '<li>I pledge to forward to the UCLouvain Registration Service any changes to the data in my file</li></ul>'
    )

    @classmethod
    def recuperer(
        cls,
        proposition: Union['PropositionDoctorale', 'PropositionGenerale', 'PropositionContinue'],
        formation_translator: 'IFormationTranlator',
        profil_candidat_translator: 'IProfilCandidatTranslator',
    ) -> List['ElementConfirmation']:
        elements = []
        # Confirmation de l'année académique concernée
        if proposition.annee_calculee and proposition.annee_calculee > proposition.formation_id.annee:
            elements.append(
                ElementConfirmation(
                    nom='hors_delai',
                    texte=cls.HORS_DELAI % {'year': f"{proposition.annee_calculee}-{proposition.annee_calculee - 1}"},
                )
            )
        elements += [
            # Règlement général des études
            ElementConfirmation(
                nom='reglement_general',
                titre=_("General Study Regulations"),
                texte=cls.REGLEMENT_GENERAL,
            ),
            # Protection des données
            ElementConfirmation(
                nom='protection_donnees',
                titre=_("Data protection"),
                texte=cls.PROTECTION_DONNEES,
            ),
            # Accès aux professions réglementées
            ElementConfirmation(
                nom='professions_reglementees',
                titre=_("Access to regulated professions"),
                texte=cls.PROFESSIONS_REGLEMENTEES,
            ),
        ]

        # Frais de dossier
        if (
            # excepté doctorat et formations continues
            isinstance(proposition, PropositionGenerale)
            and isinstance(formation_translator, IFormationGeneraleTranslator)
            # excepté candidats VIP ou en modification/réorientation
            and proposition.pot_calcule
            not in [
                Pool.ADMISSION_POOL_NON_RESIDENT_QUOTA,
                Pool.ADMISSION_POOL_VIP,
                Pool.ADMISSION_POOL_EXTERNAL_ENROLLMENT_CHANGE,
                Pool.ADMISSION_POOL_EXTERNAL_REORIENTATION,
            ]
            # non-assimilé
            and proposition.comptabilite.type_situation_assimilation == TypeSituationAssimilation.AUCUNE_ASSIMILATION
            # excepté master de spécialisation
            and formation_translator.get(proposition.formation_id).type != TrainingType.MASTER_MC
            # et HUE
            and not profil_candidat_translator.get_identification(
                proposition.matricule_candidat
            ).pays_nationalite_europeen
        ):
            elements.append(
                ElementConfirmation(
                    nom='frais_dossier',
                    titre=_("Application fees"),
                    texte=cls.FRAIS_DOSSIER,
                )
            )

        if cls.est_bachelier_ou_master_en_medecine_dentisterie(proposition, formation_translator):
            elements += [
                # Convention cadre de stages
                ElementConfirmation(
                    nom='convention_cadre_stages',
                    titre=_("Internship framework agreement"),
                    texte=cls.CONVENTION_CADRE_STAGE,
                ),
                # Communication avec les Hôpitaux d'accueil
                ElementConfirmation(
                    nom='communication_hopitaux',
                    titre=_("Communication with Host Hospitals"),
                    texte=cls.COMMUNICATION_HOPITAUX,
                ),
            ]

        # Documents spécifiques aux études contingentées
        if proposition.pot_calcule == AcademicCalendarTypes.ADMISSION_POOL_NON_RESIDENT_QUOTA:
            elements.append(
                ElementConfirmation(
                    nom='documents_etudes_contingentees',
                    titre=_("Specific documents for quota studies"),
                    texte=cls.DOCUMENTS_ETUDES_CONTINGENTEES,
                )
            )

        # Communication avec votre école secondaire
        if (
            cls.est_candidat_avec_etudes_secondaires_belges_francophones(proposition.matricule_candidat)
            # formations continues non concernés
            and not isinstance(proposition, PropositionContinue)
        ):
            elements.append(
                ElementConfirmation(
                    nom='communication_ecole_secondaire',
                    titre=_("Communication with your secondary school"),
                    reponses=[_("I authorise"), _("I do not authorize")],
                    texte=cls.COMMUNICATION_ECOLE_SECONDAIRE,
                    type="radio",
                )
            )
        elements += [
            # Justificatifs
            ElementConfirmation(
                nom='justificatifs',
                titre=_("Supporting documents"),
                texte=cls.JUSTIFICATIFS,
            ),
            # Déclaration sur l'honneur
            ElementConfirmation(
                nom='declaration_sur_lhonneur',
                titre=_("I declare on my honour that"),
                texte=cls.DECLARATION_SUR_LHONNEUR,
            ),
        ]
        return elements

    @classmethod
    def est_candidat_avec_etudes_secondaires_belges_francophones(cls, matricule: str) -> bool:
        raise NotImplementedError

    @classmethod
    def valider(
        cls,
        soumis: Dict[str, str],
        proposition: Union['PropositionDoctorale', 'PropositionGenerale', 'PropositionContinue'],
        formation_translator: 'IFormationTranlator',
        profil_candidat_translator: 'IProfilCandidatTranslator',
    ) -> None:
        attendu = cls.recuperer(proposition, formation_translator, profil_candidat_translator)
        if len(soumis) != len(attendu):
            raise ElementsConfirmationNonConcordants
        for element in attendu:
            if element.type == 'checkbox' and soumis.get(element.nom) != element.texte:
                raise ElementsConfirmationNonConcordants
            elif element.reponses and soumis.get(element.nom) not in [f"{r} {element.texte}" for r in element.reponses]:
                raise ElementsConfirmationNonConcordants

    @classmethod
    def est_bachelier_ou_master_en_medecine_dentisterie(
        cls,
        proposition: Union['PropositionDoctorale', 'PropositionGenerale', 'PropositionContinue'],
        formation_translator: 'IFormationTranlator',
    ) -> bool:
        if (
            not isinstance(proposition, PropositionGenerale)
            or not isinstance(formation_translator, IFormationGeneraleTranslator)
            or not proposition.annee_calculee
        ):
            return False
        formation = formation_translator.get(proposition.formation_id)
        return formation.est_formation_medecine_ou_dentisterie and formation.type in [
            TrainingType.BACHELOR,
            TrainingType.MASTER_MA_120,
            TrainingType.MASTER_MD_120,
            TrainingType.MASTER_MS_120,
            TrainingType.MASTER_MS_180_240,
            TrainingType.MASTER_M1,
            TrainingType.MASTER_MC,
        ]
