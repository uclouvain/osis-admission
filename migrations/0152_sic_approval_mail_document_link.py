from django.db import migrations
from osis_mail_template import MailTemplateMigration

from admission.mail_templates.checklist import ADMISSION_EMAIL_SIC_APPROVAL


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0151_fix_birth_date_submitted_profile'),
    ]

    operations = [
        MailTemplateMigration(
            ADMISSION_EMAIL_SIC_APPROVAL,
            {
                'en': 'Enrolment authorisation ({admission_reference})',
                'fr-be': "Autorisation d'inscription suite à une demande d'admission ({admission_reference})",
            },
            {
                'en': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>
            <br>

            <p>
                We are pleased to inform you that you are authorised to enrol in the {training_title} 
                ({training_campus}) - {training_acronym} for the {academic_year} academic year.
            </p>

            <p>
                Please download your enrolment authorisation which contains all the relevant information and any 
                conditions that need to be met before registering.
            </p>

            <div style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <p style="border: 1px solid #dc3545; padding: 10px; border-radius: 10px; display: inline-block; width: fit-content;">
                    <img
                        width="30"
                        height="30"
                        style="width: 30px; height: 30px; outline: none; vertical-align: middle;"
                        src="data:image/svg+xml;base64,
                        PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzODQg
                        NTEyIj48IS0tIUZvbnQgQXdlc29tZSBGcmVlIDYuNS4xIGJ5IEBmb250YXdlc29tZSAtIGh0dHBz
                        Oi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNl
                        bnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjQgRm9udGljb25zLCBJbmMuLS0+PHBhdGggZmlsbD0iI2Rj
                        MzU0NSIgZD0iTTM2OS45IDk3LjlMMjg2IDE0QzI3NyA1IDI2NC44LS4xIDI1Mi4xLS4xSDQ4QzIx
                        LjUgMCAwIDIxLjUgMCA0OHY0MTZjMCAyNi41IDIxLjUgNDggNDggNDhoMjg4YzI2LjUgMCA0OC0y
                        MS41IDQ4LTQ4VjEzMS45YzAtMTIuNy01LjEtMjUtMTQuMS0zNHpNMzMyLjEgMTI4SDI1NlY1MS45
                        bDc2LjEgNzYuMXpNNDggNDY0VjQ4aDE2MHYxMDRjMCAxMy4zIDEwLjcgMjQgMjQgMjRoMTA0djI4
                        OEg0OHptMjUwLjItMTQzLjdjLTEyLjItMTItNDctOC43LTY0LjQtNi41LTE3LjItMTAuNS0yOC43
                        LTI1LTM2LjgtNDYuMyAzLjktMTYuMSAxMC4xLTQwLjYgNS40LTU2LTQuMi0yNi4yLTM3LjgtMjMu
                        Ni00Mi42LTUuOS00LjQgMTYuMS0uNCAzOC41IDcgNjcuMS0xMCAyMy45LTI0LjkgNTYtMzUuNCA3
                        NC40LTIwIDEwLjMtNDcgMjYuMi01MSA0Ni4yLTMuMyAxNS44IDI2IDU1LjIgNzYuMS0zMS4yIDIy
                        LjQtNy40IDQ2LjgtMTYuNSA2OC40LTIwLjEgMTguOSAxMC4yIDQxIDE3IDU1LjggMTcgMjUuNSAw
                        IDI4LTI4LjIgMTcuNS0zOC43em0tMTk4LjEgNzcuOGM1LjEtMTMuNyAyNC41LTI5LjUgMzAuNC0z
                        NS0xOSAzMC4zLTMwLjQgMzUuNy0zMC40IDM1em04MS42LTE5MC42YzcuNCAwIDYuNyAzMi4xIDEu
                        OCA0MC44LTQuNC0xMy45LTQuMy00MC44LTEuOC00MC44em0tMjQuNCAxMzYuNmM5LjctMTYuOSAx
                        OC0zNyAyNC43LTU0LjcgOC4zIDE1LjEgMTguOSAyNy4yIDMwLjEgMzUuNS0yMC44IDQuMy0zOC45
                        IDEzLjEtNTQuOCAxOS4yem0xMzEuNi01cy01IDYtMzcuMy03LjhjMzUuMS0yLjYgNDAuOSA1LjQg
                        MzcuMyA3Ljh6Ii8+PC9zdmc+"
                        alt="Link of the enrolment authorisation"
                    />
                    <a
                        href="{enrollment_authorization_document_link}"
                        target="_blank"
                        style="color: #dc3545;
                        background-color: transparent;
                        background-image: none;
                        display: inline-block;
                        font-weight: 400;
                        white-space: nowrap;
                        vertical-align: middle;
                        user-select: none;"
                    >Enrolment authorisation</a>
                </p>
            </div>

            <p>
                If you require a student visa, please use the enrolment authorisation and the visa application to 
                apply via your local Belgian embassy or consulate. For more information, 
                consult the <a href="https://dofi.ibz.be/en" target="_blank" style="color: #0000EE;">Belgian Immigration Office</a>.
            </p>

            <div style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <p style="border: 1px solid #dc3545; padding: 10px; border-radius: 10px; display: inline-block; width: fit-content;">
                    <img
                        width="30"
                        height="30"
                        style="width: 30px; height: 30px; outline: none; vertical-align: middle;"
                        src="data:image/svg+xml;base64,
                        PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzODQg
                        NTEyIj48IS0tIUZvbnQgQXdlc29tZSBGcmVlIDYuNS4xIGJ5IEBmb250YXdlc29tZSAtIGh0dHBz
                        Oi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNl
                        bnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjQgRm9udGljb25zLCBJbmMuLS0+PHBhdGggZmlsbD0iI2Rj
                        MzU0NSIgZD0iTTM2OS45IDk3LjlMMjg2IDE0QzI3NyA1IDI2NC44LS4xIDI1Mi4xLS4xSDQ4QzIx
                        LjUgMCAwIDIxLjUgMCA0OHY0MTZjMCAyNi41IDIxLjUgNDggNDggNDhoMjg4YzI2LjUgMCA0OC0y
                        MS41IDQ4LTQ4VjEzMS45YzAtMTIuNy01LjEtMjUtMTQuMS0zNHpNMzMyLjEgMTI4SDI1NlY1MS45
                        bDc2LjEgNzYuMXpNNDggNDY0VjQ4aDE2MHYxMDRjMCAxMy4zIDEwLjcgMjQgMjQgMjRoMTA0djI4
                        OEg0OHptMjUwLjItMTQzLjdjLTEyLjItMTItNDctOC43LTY0LjQtNi41LTE3LjItMTAuNS0yOC43
                        LTI1LTM2LjgtNDYuMyAzLjktMTYuMSAxMC4xLTQwLjYgNS40LTU2LTQuMi0yNi4yLTM3LjgtMjMu
                        Ni00Mi42LTUuOS00LjQgMTYuMS0uNCAzOC41IDcgNjcuMS0xMCAyMy45LTI0LjkgNTYtMzUuNCA3
                        NC40LTIwIDEwLjMtNDcgMjYuMi01MSA0Ni4yLTMuMyAxNS44IDI2IDU1LjIgNzYuMS0zMS4yIDIy
                        LjQtNy40IDQ2LjgtMTYuNSA2OC40LTIwLjEgMTguOSAxMC4yIDQxIDE3IDU1LjggMTcgMjUuNSAw
                        IDI4LTI4LjIgMTcuNS0zOC43em0tMTk4LjEgNzcuOGM1LjEtMTMuNyAyNC41LTI5LjUgMzAuNC0z
                        NS0xOSAzMC4zLTMwLjQgMzUuNy0zMC40IDM1em04MS42LTE5MC42YzcuNCAwIDYuNyAzMi4xIDEu
                        OCA0MC44LTQuNC0xMy45LTQuMy00MC44LTEuOC00MC44em0tMjQuNCAxMzYuNmM5LjctMTYuOSAx
                        OC0zNyAyNC43LTU0LjcgOC4zIDE1LjEgMTguOSAyNy4yIDMwLjEgMzUuNS0yMC44IDQuMy0zOC45
                        IDEzLjEtNTQuOCAxOS4yem0xMzEuNi01cy01IDYtMzcuMy03LjhjMzUuMS0yLjYgNDAuOSA1LjQg
                        MzcuMyA3Ljh6Ii8+PC9zdmc+"
                        alt="Link of the visa application form"
                    />
                    <a
                        href="{visa_application_document_link}"
                        target="_blank"
                        style="color: #dc3545;
                        background-color: transparent;
                        background-image: none;
                        display: inline-block;
                        font-weight: 400;
                        white-space: nowrap;
                        vertical-align: middle;
                        user-select: none;"
                    >Visa application form</a>
                </p>
            </div>

            <p>
                After you have obtained your visa, please send us the signed enrolment authorisation and any 
                additional documents to the email address below. These documents are required to finalise your 
                enrolment.
            </p>

            <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <img
                    width="20" 
                    height="20" 
                    style="width: 20px; height: 20px; outline: none; vertical-align: middle;" 
                    src="data:image/svg+xml;base64, 
                    PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1MTIg
                    NTEyIj48IS0tIUZvbnQgQXdlc29tZSBGcmVlIDYuNS4xIGJ5IEBmb250YXdlc29tZSAtIGh0dHBz
                    Oi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNl
                    bnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjQgRm9udGljb25zLCBJbmMuLS0+PHBhdGggZmlsbD0iIzAw
                    MDBlZSIgZD0iTTQ2NCA2NEg0OEMyMS41IDY0IDAgODUuNSAwIDExMnYyODhjMCAyNi41IDIxLjUg
                    NDggNDggNDhoNDE2YzI2LjUgMCA0OC0yMS41IDQ4LTQ4VjExMmMwLTI2LjUtMjEuNS00OC00OC00
                    OHptMCA0OHY0MC44Yy0yMi40IDE4LjMtNTguMiA0Ni43LTEzNC42IDEwNi41LTE2LjggMTMuMi01
                    MC4yIDQ1LjEtNzMuNCA0NC43LTIzLjIgLjQtNTYuNi0zMS41LTczLjQtNDQuN0MxMDYuMiAxOTku
                    NSA3MC40IDE3MS4xIDQ4IDE1Mi44VjExMmg0MTZ6TTQ4IDQwMFYyMTQuNGMyMi45IDE4LjMgNTUu
                    NCA0My45IDEwNC45IDgyLjYgMjEuOSAxNy4yIDYwLjEgNTUuMiAxMDMuMSA1NSA0Mi43IC4yIDgw
                    LjUtMzcuMiAxMDMuMS01NC45IDQ5LjUtMzguOCA4Mi02NC40IDEwNC45LTgyLjdWNDAwSDQ4eiIv
                    Pjwvc3ZnPg=="
                    alt="The Enrolment Office email address"
                />
                <a href="mailto:{admission_email}" target="_blank" style="color: #0000EE;">{admission_email}</a>
            </p>

            <p>
                For enrolment questions, please see 
                <a href="https://uclouvain.be/en/study/inscriptions" target="_blank" style="color: #0000EE;">our website</a>.
            </p>

            <p>
                The <a href="https://uclouvain.be/en/study/academic-calendar-1.html" target="_blank" style="color: #0000EE;">academic year</a> 
                begins on {academic_year_start_date}.
            </p>

            <p>
                For questions concerning your arrival in Belgium, please see 
                <a href="https://uclouvain.be/en/study/inscriptions/welcome-to-international-students.html" target="_blank" style="color: #0000EE;">
                our international students webpage</a>.
            </p>

            <p>
                Welcome to UCLouvain.
            </p>
            <br>

            <p>
                Sincerely,
            </p>

            <p>
                The Enrolment Office
            </p>
            ''',
                'fr-be': '''<p>{greetings} {candidate_first_name} {candidate_last_name},</p>
            <br>

            <p>
                Nous avons le plaisir de vous informer que vous êtes autorisé·e à vous inscrire au programme 
                {training_title} ({training_campus}) - {training_acronym} pour l'année académique {academic_year}.
            </p>

            <p>
                Veuillez télécharger votre autorisation d'inscription qui comprend toutes les informations utiles et 
                les éventuelles conditions à remplir préalablement à votre inscription.
            </p>

            <div style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <p style="border: 1px solid #dc3545; padding: 10px; border-radius: 10px; display: inline-block; width: fit-content;">
                    <img
                        width="30"
                        height="30"
                        style="width: 30px; height: 30px; outline: none; vertical-align: middle;"
                        src="data:image/svg+xml;base64,
                        PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzODQg
                        NTEyIj48IS0tIUZvbnQgQXdlc29tZSBGcmVlIDYuNS4xIGJ5IEBmb250YXdlc29tZSAtIGh0dHBz
                        Oi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNl
                        bnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjQgRm9udGljb25zLCBJbmMuLS0+PHBhdGggZmlsbD0iI2Rj
                        MzU0NSIgZD0iTTM2OS45IDk3LjlMMjg2IDE0QzI3NyA1IDI2NC44LS4xIDI1Mi4xLS4xSDQ4QzIx
                        LjUgMCAwIDIxLjUgMCA0OHY0MTZjMCAyNi41IDIxLjUgNDggNDggNDhoMjg4YzI2LjUgMCA0OC0y
                        MS41IDQ4LTQ4VjEzMS45YzAtMTIuNy01LjEtMjUtMTQuMS0zNHpNMzMyLjEgMTI4SDI1NlY1MS45
                        bDc2LjEgNzYuMXpNNDggNDY0VjQ4aDE2MHYxMDRjMCAxMy4zIDEwLjcgMjQgMjQgMjRoMTA0djI4
                        OEg0OHptMjUwLjItMTQzLjdjLTEyLjItMTItNDctOC43LTY0LjQtNi41LTE3LjItMTAuNS0yOC43
                        LTI1LTM2LjgtNDYuMyAzLjktMTYuMSAxMC4xLTQwLjYgNS40LTU2LTQuMi0yNi4yLTM3LjgtMjMu
                        Ni00Mi42LTUuOS00LjQgMTYuMS0uNCAzOC41IDcgNjcuMS0xMCAyMy45LTI0LjkgNTYtMzUuNCA3
                        NC40LTIwIDEwLjMtNDcgMjYuMi01MSA0Ni4yLTMuMyAxNS44IDI2IDU1LjIgNzYuMS0zMS4yIDIy
                        LjQtNy40IDQ2LjgtMTYuNSA2OC40LTIwLjEgMTguOSAxMC4yIDQxIDE3IDU1LjggMTcgMjUuNSAw
                        IDI4LTI4LjIgMTcuNS0zOC43em0tMTk4LjEgNzcuOGM1LjEtMTMuNyAyNC41LTI5LjUgMzAuNC0z
                        NS0xOSAzMC4zLTMwLjQgMzUuNy0zMC40IDM1em04MS42LTE5MC42YzcuNCAwIDYuNyAzMi4xIDEu
                        OCA0MC44LTQuNC0xMy45LTQuMy00MC44LTEuOC00MC44em0tMjQuNCAxMzYuNmM5LjctMTYuOSAx
                        OC0zNyAyNC43LTU0LjcgOC4zIDE1LjEgMTguOSAyNy4yIDMwLjEgMzUuNS0yMC44IDQuMy0zOC45
                        IDEzLjEtNTQuOCAxOS4yem0xMzEuNi01cy01IDYtMzcuMy03LjhjMzUuMS0yLjYgNDAuOSA1LjQg
                        MzcuMyA3Ljh6Ii8+PC9zdmc+"
                        alt="Lien de l'autorisation d'inscription"
                    />
                    <a
                        href="{enrollment_authorization_document_link}"
                        target="_blank"
                        style="color: #dc3545;
                        background-color: transparent;
                        background-image: none;
                        display: inline-block;
                        font-weight: 400;
                        white-space: nowrap;
                        vertical-align: middle;
                        user-select: none;"
                    >Autorisation d'inscription</a>
                </p>
            </div>

            <p>
                Si vous êtes concerné·e par l'obtention d'un visa d'études, l'autorisation d'inscription accompagnée du 
                formulaire pour la demande de visa vous permettent d'entamer ces démarches auprès de l'ambassade ou du 
                consulat de Belgique local·e. Nous vous invitons à consulter le 
                <a href="https://dofi.ibz.be/fr" target="_blank" style="color: #0000EE;">site officiel de l'Office des étrangers</a>.
            </p>

            <div style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <p style="border: 1px solid #dc3545; padding: 10px; border-radius: 10px; display: inline-block; width: fit-content;">
                    <img
                        width="30"
                        height="30"
                        style="width: 30px; height: 30px; outline: none; vertical-align: middle;"
                        src="data:image/svg+xml;base64,
                        PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzODQg
                        NTEyIj48IS0tIUZvbnQgQXdlc29tZSBGcmVlIDYuNS4xIGJ5IEBmb250YXdlc29tZSAtIGh0dHBz
                        Oi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNl
                        bnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjQgRm9udGljb25zLCBJbmMuLS0+PHBhdGggZmlsbD0iI2Rj
                        MzU0NSIgZD0iTTM2OS45IDk3LjlMMjg2IDE0QzI3NyA1IDI2NC44LS4xIDI1Mi4xLS4xSDQ4QzIx
                        LjUgMCAwIDIxLjUgMCA0OHY0MTZjMCAyNi41IDIxLjUgNDggNDggNDhoMjg4YzI2LjUgMCA0OC0y
                        MS41IDQ4LTQ4VjEzMS45YzAtMTIuNy01LjEtMjUtMTQuMS0zNHpNMzMyLjEgMTI4SDI1NlY1MS45
                        bDc2LjEgNzYuMXpNNDggNDY0VjQ4aDE2MHYxMDRjMCAxMy4zIDEwLjcgMjQgMjQgMjRoMTA0djI4
                        OEg0OHptMjUwLjItMTQzLjdjLTEyLjItMTItNDctOC43LTY0LjQtNi41LTE3LjItMTAuNS0yOC43
                        LTI1LTM2LjgtNDYuMyAzLjktMTYuMSAxMC4xLTQwLjYgNS40LTU2LTQuMi0yNi4yLTM3LjgtMjMu
                        Ni00Mi42LTUuOS00LjQgMTYuMS0uNCAzOC41IDcgNjcuMS0xMCAyMy45LTI0LjkgNTYtMzUuNCA3
                        NC40LTIwIDEwLjMtNDcgMjYuMi01MSA0Ni4yLTMuMyAxNS44IDI2IDU1LjIgNzYuMS0zMS4yIDIy
                        LjQtNy40IDQ2LjgtMTYuNSA2OC40LTIwLjEgMTguOSAxMC4yIDQxIDE3IDU1LjggMTcgMjUuNSAw
                        IDI4LTI4LjIgMTcuNS0zOC43em0tMTk4LjEgNzcuOGM1LjEtMTMuNyAyNC41LTI5LjUgMzAuNC0z
                        NS0xOSAzMC4zLTMwLjQgMzUuNy0zMC40IDM1em04MS42LTE5MC42YzcuNCAwIDYuNyAzMi4xIDEu
                        OCA0MC44LTQuNC0xMy45LTQuMy00MC44LTEuOC00MC44em0tMjQuNCAxMzYuNmM5LjctMTYuOSAx
                        OC0zNyAyNC43LTU0LjcgOC4zIDE1LjEgMTguOSAyNy4yIDMwLjEgMzUuNS0yMC44IDQuMy0zOC45
                        IDEzLjEtNTQuOCAxOS4yem0xMzEuNi01cy01IDYtMzcuMy03LjhjMzUuMS0yLjYgNDAuOSA1LjQg
                        MzcuMyA3Ljh6Ii8+PC9zdmc+"
                        alt="Lien du formulaire pour la demande de visa"
                    />
                    <a
                        href="{visa_application_document_link}"
                        target="_blank"
                        style="color: #dc3545;
                        background-color: transparent;
                        background-image: none;
                        display: inline-block;
                        font-weight: 400;
                        white-space: nowrap;
                        vertical-align: middle;
                        user-select: none;"
                    >Formulaire pour la demande de visa</a>
                </p>
            </div>

            <p>
                Afin de finaliser votre inscription à l'Université, nous vous remercions de nous transmettre 
                l'autorisation signée ainsi que les éventuels documents complémentaires à l'adresse ci-dessous. 
                Nous vous rappelons qu'il est impératif de nous renvoyer ces documents après l'obtention de votre visa.
            </p>

            <p style="text-align: center; padding-top: 5px; padding-bottom: 10px;">
                <img
                    width="20"
                    height="20"
                    style="width: 20px; height: 20px; outline: none; vertical-align: middle;"
                    src="data:image/svg+xml;base64, 
                    PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1MTIg
                    NTEyIj48IS0tIUZvbnQgQXdlc29tZSBGcmVlIDYuNS4xIGJ5IEBmb250YXdlc29tZSAtIGh0dHBz
                    Oi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNl
                    bnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjQgRm9udGljb25zLCBJbmMuLS0+PHBhdGggZmlsbD0iIzAw
                    MDBlZSIgZD0iTTQ2NCA2NEg0OEMyMS41IDY0IDAgODUuNSAwIDExMnYyODhjMCAyNi41IDIxLjUg
                    NDggNDggNDhoNDE2YzI2LjUgMCA0OC0yMS41IDQ4LTQ4VjExMmMwLTI2LjUtMjEuNS00OC00OC00
                    OHptMCA0OHY0MC44Yy0yMi40IDE4LjMtNTguMiA0Ni43LTEzNC42IDEwNi41LTE2LjggMTMuMi01
                    MC4yIDQ1LjEtNzMuNCA0NC43LTIzLjIgLjQtNTYuNi0zMS41LTczLjQtNDQuN0MxMDYuMiAxOTku
                    NSA3MC40IDE3MS4xIDQ4IDE1Mi44VjExMmg0MTZ6TTQ4IDQwMFYyMTQuNGMyMi45IDE4LjMgNTUu
                    NCA0My45IDEwNC45IDgyLjYgMjEuOSAxNy4yIDYwLjEgNTUuMiAxMDMuMSA1NSA0Mi43IC4yIDgw
                    LjUtMzcuMiAxMDMuMS01NC45IDQ5LjUtMzguOCA4Mi02NC40IDEwNC45LTgyLjdWNDAwSDQ4eiIv
                    Pjwvc3ZnPg=="
                    alt="Adresse email du service d'inscription"
                />
                <a href="mailto:{admission_email}" target="_blank" style="color: #0000EE;">
                    {admission_email}
                </a>
            </p>

            <p>
                Pour toute question relative à l'inscription, nous vous invitons à consulter 
                <a href="https://uclouvain.be/fr/etudier/inscriptions" target="_blank" style="color: #0000EE;">notre site</a>.
            </p>

            <p>
                Nous vous informons que le début de l'année académique est fixé au {academic_year_start_date} 
                (<a href="https://uclouvain.be/fr/etudier/calendrier-academique.html" target="_blank" style="color: #0000EE;">Calendrier 
                académique</a>).
            </p>

            <p>
                Si vous avez des questions concernant votre arrivée en Belgique, vous avez à votre disposition 
                toute une série d'informations sur 
                <a href="https://uclouvain.be/fr/etudier/inscriptions/bienvenue-aux-etudiants-internationaux-et-aux-etudiantes-internationales.html" target="_blank" style="color: #0000EE;">
                notre page</a>.
            </p>

            <p>
                Nous vous souhaitons la bienvenue à l'UCLouvain.
            </p>
            <br>

            <p>
                Veuillez agréer l'expression de nos salutations distinguées.
            </p>

            <p>
                Le Service des inscriptions
            </p>
            ''',
            },
        ),
    ]
