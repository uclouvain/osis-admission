# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.utils.translation import gettext_lazy as _, pgettext_lazy

from base.models.utils.utils import ChoiceEnum


class ChoixStatutPropositionContinue(ChoiceEnum):
    EN_BROUILLON = _('In draft form')
    CONFIRMEE = _('Application confirmed')
    EN_ATTENTE = _('On hold')
    INSCRIPTION_REFUSEE = _('Application denied')
    ANNULEE = _('Cancelled application')
    INSCRIPTION_AUTORISEE = _('Application accepted')
    CLOTUREE = _('Closed')
    ANNULEE_PAR_GESTIONNAIRE = _('Cancelled application by a manager')


class ChoixInscriptionATitre(ChoiceEnum):
    PRIVE = _('Private')
    PROFESSIONNEL = _('Professional')


class ChoixTypeAdresseFacturation(ChoiceEnum):
    RESIDENTIEL = _("Legal domicile")
    CONTACT = pgettext_lazy("admission", "Postal address")
    AUTRE = _("Other address")


class ChoixMoyensDecouverteFormation(ChoiceEnum):
    SITE_WEB_UCLOUVAIN = _("Via the website of UCLouvain")
    SITE_FORMATION_CONTINUE = _("Via the website of the continuing education")
    PRESSE = _("On the press")
    FACEBOOK = _("Via Facebook")
    LINKEDIN = _("Via LinkedIn")
    COURRIER_PERSONNALISE = _("Via a personalized letter")
    EMAILING = _("Via an emailing")
    BOUCHE_A_OREILLE = _("Via word of mouth")
    AMIS = _("Via friends")
    ANCIENS_ETUDIANTS = _("Via former students")
    MOOCS = _("Via MOOCs")
    AUTRE = _("Other")


STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE = {
    ChoixStatutPropositionContinue.EN_BROUILLON.name,
    ChoixStatutPropositionContinue.ANNULEE.name,
}

STATUTS_PROPOSITION_CONTINUE_SOUMISE = (
    set(ChoixStatutPropositionContinue.get_names()) - STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE
)


class ChoixStatutChecklist(ChoiceEnum):
    INITIAL_NON_CONCERNE = _("INITIAL_NON_CONCERNE")
    INITIAL_CANDIDAT = _("INITIAL_CANDIDAT")
    GEST_EN_COURS = _("GEST_EN_COURS")
    GEST_BLOCAGE = _("GEST_BLOCAGE")
    GEST_BLOCAGE_ULTERIEUR = _("GEST_BLOCAGE_ULTERIEUR")
    GEST_REUSSITE = _("GEST_REUSSITE")
    SYST_REUSSITE = _("SYST_REUSSITE")


class ChoixMotifRefus(ChoiceEnum):
    PARCOURS_NON_ADAPTE = _("Your background is not suited to this course")
    CONDITIONS = _("You do not meet the admission requirements")
    FULL = _("The programme is already full")
    EXPERIENCE = _("Your experience and reasons for undertaking this programme are insufficient")
    AUTRE = _("Other")


class ChoixMotifAttente(ChoiceEnum):
    COMPLET = _("The programme is already full")
    VERIFICATION = _("Your application is currently being reviewed by the course exam board")
    AUTRE = _("Other")


class ChoixEdition(ChoiceEnum):
    UN = "1"
    DEUX = "2"
    TROIS = "3"
    QUATRE = "4"
    CINQ = "5"
    SIX = "6"


class OngletsChecklist(ChoiceEnum):
    fiche_etudiant = _("Student report")
    decision = _("Decision")
