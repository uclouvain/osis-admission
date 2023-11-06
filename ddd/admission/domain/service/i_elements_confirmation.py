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
from typing import Dict, List, Optional, Union

import attr
from django.utils.translation import gettext_lazy as _

from admission.ddd import PLUS_5_ISO_CODES, BE_ISO_CODE
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
        'In accordance with the information at <a target="_blank" href="'
        'https://uclouvain.be/en/study/inscriptions/reglementations.html">'
        'https://uclouvain.be/en/study/inscriptions/reglementations.html</a>, '
        'I declare that I have read the university regulations '
        'and accept their terms.'
    )
    PROTECTION_DONNEES = _(
        'In accordance with the information at <a target="_blank" href="'
        'https://uclouvain.be/en/study/inscriptions/vie-privee.html">'
        'https://uclouvain.be/en/study/inscriptions/vie-privee.html</a>, '
        'I declare that I have read the data protection policy of the Universite catholique de Louvain and accept '
        'its terms.'
    )
    PROFESSIONS_REGLEMENTEES = _(
        'In accordance with the information at <a target="_blank" href="'
        'https://uclouvain.be/en/study/inscriptions/acces-aux-professions-reglementees.html">'
        'https://uclouvain.be/en/study/inscriptions/acces-aux-professions-reglementees.html</a>, I declare that, if '
        'the courses listed therein concern me, I have received the information relating to their requirements '
        'for admission or continuation and to the specific rules or restrictions of accreditation or professional '
        'establishment to which the professional or accredited title is subject and I accept the terms thereof.'
    )
    FRAIS_DOSSIER = _(
        'I am aware that as an applicant without a European Union nationality or Belgian student status, '
        'I am required to pay an application fee of &euro;200 via online payment. The application fee must be '
        'received by UCLouvain within 15 calendar days. Otherwise, my application will not be considered. '
        'For more information: '
        '<a href="https://uclouvain.be/en/study/inscriptions/tuition-fees-non-eu-students.html" '
        'target="_blank">https://uclouvain.be/en/study/inscriptions/tuition-fees-non-eu-students.html</a>.'
    )
    CONVENTION_CADRE_STAGE = _(
        'I have read and understood the latest version of the Internship Framework Agreement between '
        'UCLouvain and the Host Hospitals drawn up as part of the UCLouvain bachelor\'s or master\'s '
        'course in medicine with a view to acquiring the corresponding course units, and I undertake '
        'to comply with its terms: '
        '<a href="https://cdn.uclouvain.be/groups/cms-editors-mede/ConventionStageMed.pdf" '
        'target="_blank">https://cdn.uclouvain.be/groups/cms-editors-mede/ConventionStageMed.pdf</a>'
    )
    COMMUNICATION_HOPITAUX = _(
        'I am aware that the UCLouvain Faculty of Medicine and Dentistry has provided certain personal details'
        ' (surname(s), first name(s), NOMA, date of birth, place of birth, address) to the Host Hospitals in '
        'order to establish the various user rights that I will need as part of my internships, in compliance '
        'with the General Data Protection Regulation (GDPR) and the law of 30 July 2018 on the protection of '
        'individuals with regard to the processing of personal data. My data is kept for the time necessary '
        'for the proper performance of the internship and is never transmitted to parties other than '
        'those mentioned above. Appropriate technical and organisational measures are put in place to ensure an '
        'adequate level of protection for this data.'
    )
    DOCUMENTS_ETUDES_CONTINGENTEES = _(
        'I am aware that no additional documents specific to limited-enrolment courses can be added once '
        'my online application has been confirmed.'
    )
    VISA = _(
        'I am aware that the university may verify with third parties all of the application information I provide. '
        'In this context, I understand UCLouvain reserves the right to send the information or documents in '
        'my application to the selected diplomatic post (e.g. diplomas, transcripts, enrolment authorisation, etc.) '
        'in order to ensure their authenticity.'
    )
    COMMUNICATION_ECOLE_SECONDAIRE = _(
        'UCLouvain to forward to the secondary school at which I obtained my Belgian secondary school, '
        'information relating to the successful completion of the first year of the bachelor\'s course, '
        'and any academic degree obtained with the possible mention of'
    )
    JUSTIFICATIFS = _(
        'I undertake to send any supporting documents requested %(by_service)s <strong>within 15 calendar '
        'days</strong>. If I fail to do so, I acknowledge and accept that my application will be considered '
        'inadmissible in accordance with Article 9 of the Academic Regulations and Procedures (RGEE).'
    )
    DECLARATION_SUR_LHONNEUR = _(
        '<ul><li>the information I have provided is accurate and complete. UCLouvain reserves the right to verify '
        'the information contained in the application with third parties</li>'
        '<li>I have uploaded all relevant documents confirming the information provided</li>'
        '<li>I undertake to inform %(to_service)s of any changes to the information in my application</li></ul>'
    )
    DROITS_INSCRIPTION_IUFC = _(
        'By finalising my application, I undertake to pay the registration fees upon receipt of the invoice '
        '(provided my application is accepted). In case of cancellation, the modalities depend on the Faculties.'
    )
    TITRE_ELEMENT_CONFIRMATION = {
        'hors_delai': '',
        'reglement_general': _("Academic Regulations"),
        'protection_donnees': _("Data protection"),
        'professions_reglementees': _("Admission to regulated professions"),
        'frais_dossier': _("Application fee"),
        'convention_cadre_stages': _("Internship Framework Agreement"),
        'communication_hopitaux': _("Communication with Host Hospitals"),
        'documents_etudes_contingentees': _("Documents specific to limited-enrolment courses"),
        'communication_ecole_secondaire': _("Communication with your secondary school"),
        'justificatifs': _("Supporting documents"),
        'declaration_sur_lhonneur': _("I hereby declare that"),
        'droits_inscription_iufc': _("Registration fees"),
        'visa': _("Communication with the diplomatic post for your visa application"),
    }

    @classmethod
    def recuperer(
        cls,
        proposition: Union['PropositionDoctorale', 'PropositionGenerale', 'PropositionContinue'],
        formation_translator: 'IFormationTranlator',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_soumise: int = None,
    ) -> List['ElementConfirmation']:
        elements = []
        identification_dto = (
            profil_candidat_translator.get_identification(proposition.matricule_candidat)
            if isinstance(proposition, PropositionGenerale)
            else None
        )

        # Confirmation de l'année académique concernée
        annee_a_prendre_en_compte = annee_soumise if annee_soumise is not None else proposition.annee_calculee
        if annee_a_prendre_en_compte and annee_a_prendre_en_compte > proposition.formation_id.annee:
            elements.append(
                ElementConfirmation(
                    nom='hors_delai',
                    texte=cls.HORS_DELAI % {'year': f"{annee_a_prendre_en_compte}-{annee_a_prendre_en_compte + 1}"},
                )
            )
        elements += [
            # Règlement général des études
            ElementConfirmation(
                nom='reglement_general',
                titre=cls.TITRE_ELEMENT_CONFIRMATION['reglement_general'],
                texte=cls.REGLEMENT_GENERAL,
            ),
            # Protection des données
            ElementConfirmation(
                nom='protection_donnees',
                titre=cls.TITRE_ELEMENT_CONFIRMATION['protection_donnees'],
                texte=cls.PROTECTION_DONNEES,
            ),
            # Accès aux professions réglementées
            ElementConfirmation(
                nom='professions_reglementees',
                titre=cls.TITRE_ELEMENT_CONFIRMATION['professions_reglementees'],
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
            and not identification_dto.pays_nationalite_europeen
        ):
            elements.append(
                ElementConfirmation(
                    nom='frais_dossier',
                    titre=cls.TITRE_ELEMENT_CONFIRMATION['frais_dossier'],
                    texte=cls.FRAIS_DOSSIER,
                )
            )

        if cls.est_bachelier_ou_master_en_medecine_dentisterie(proposition, formation_translator):
            elements += [
                # Convention cadre de stages
                ElementConfirmation(
                    nom='convention_cadre_stages',
                    titre=cls.TITRE_ELEMENT_CONFIRMATION['convention_cadre_stages'],
                    texte=cls.CONVENTION_CADRE_STAGE,
                ),
                # Communication avec les Hôpitaux d'accueil
                ElementConfirmation(
                    nom='communication_hopitaux',
                    titre=cls.TITRE_ELEMENT_CONFIRMATION['communication_hopitaux'],
                    texte=cls.COMMUNICATION_HOPITAUX,
                ),
            ]

        # Documents spécifiques aux études contingentées
        if proposition.pot_calcule == AcademicCalendarTypes.ADMISSION_POOL_NON_RESIDENT_QUOTA:
            elements.append(
                ElementConfirmation(
                    nom='documents_etudes_contingentees',
                    titre=cls.TITRE_ELEMENT_CONFIRMATION['documents_etudes_contingentees'],
                    texte=cls.DOCUMENTS_ETUDES_CONTINGENTEES,
                )
            )

        # Visa
        if isinstance(proposition, PropositionGenerale) and identification_dto.est_concerne_par_visa:
            elements.append(
                ElementConfirmation(
                    nom='visa',
                    titre=cls.TITRE_ELEMENT_CONFIRMATION['visa'],
                    texte=cls.VISA,
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
                    titre=cls.TITRE_ELEMENT_CONFIRMATION['communication_ecole_secondaire'],
                    reponses=[_("I authorise"), _("I do not authorize")],
                    texte=cls.COMMUNICATION_ECOLE_SECONDAIRE,
                    type="radio",
                )
            )
        by_service = (
            _("by the University Institute for Continuing Education (IUFC)")
            if isinstance(proposition, PropositionContinue)
            else _("by the Enrolment Office")
        )
        to_service = (
            _("the University Institute of Continuing Education")
            if isinstance(proposition, PropositionContinue)
            else _("the UCLouvain Registration Service")
        )
        elements += [
            # Justificatifs
            ElementConfirmation(
                nom='justificatifs',
                titre=cls.TITRE_ELEMENT_CONFIRMATION['justificatifs'],
                texte=cls.JUSTIFICATIFS % {'by_service': by_service},
            ),
            # Déclaration sur l'honneur
            ElementConfirmation(
                nom='declaration_sur_lhonneur',
                titre=cls.TITRE_ELEMENT_CONFIRMATION['declaration_sur_lhonneur'],
                texte=cls.DECLARATION_SUR_LHONNEUR % {'to_service': to_service},
            ),
        ]
        # Uniquement pour IUFC
        if isinstance(proposition, PropositionContinue):
            elements.append(
                ElementConfirmation(
                    nom='droits_inscription_iufc',
                    titre=cls.TITRE_ELEMENT_CONFIRMATION['droits_inscription_iufc'],
                    texte=cls.DROITS_INSCRIPTION_IUFC,
                )
            )
        return elements

    @classmethod
    def est_candidat_avec_etudes_secondaires_belges_francophones(cls, matricule: str) -> bool:
        raise NotImplementedError

    @classmethod
    def valider(
        cls,
        soumis: Dict[str, str],
        proposition: Union['PropositionDoctorale', 'PropositionGenerale', 'PropositionContinue'],
        annee_soumise: int,
        formation_translator: 'IFormationTranlator',
        profil_candidat_translator: 'IProfilCandidatTranslator',
    ) -> None:
        attendu = cls.recuperer(proposition, formation_translator, profil_candidat_translator, annee_soumise)
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
