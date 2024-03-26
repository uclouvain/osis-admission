/*
 *
 * OSIS stands for Open Student Information System. It's an application
 * designed to manage the core business of higher education institutions,
 * such as universities, faculties, institutes and professional schools.
 * The core business involves the administration of students, teachers,
 * courses, programs and so on.
 *
 * Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * A copy of this license - GNU General Public License - is available
 * at the root of the source code of this program.  If not,
 * see http://www.gnu.org/licenses/.
 *
 */

/**
 * Write content to clipboard when the user clicks on a button (requires jquery + tooltip.js from bootstrap).
 * Each clipboard element must have a button and something having a 'copy-to-clipboard-element' class from which
 * the content is copied.
 * If a 'data-html' attribute is set to 'true' on the button, the content itself is copied as html, otherwise only the
 * inner text content is copied (by default).
 * If the browser doesn't support the clipboard API, the button selects the related content.
 * @param clipboardSelector the selector of the clipboard elements.
 */
function writeTextToClipboard(clipboardSelector) {
    const tooltipTextsForCopy = {
        initial: gettext('Copy to clipboard'),
        success: gettext('Copied!'),
        failure: gettext('Impossible to copy'),
    }
    const tooltipTextsForSelection = {
        initial: gettext('Select the element'),
        success: gettext('Selected!'),
        failure: gettext('Impossible to select'),
    }

    const canUseClipboardWriteTextAPI = Boolean(navigator.clipboard && navigator.clipboard.writeText);
    const canUseClipboardWriteApi = Boolean(navigator.clipboard && navigator.clipboard.write);

    $(clipboardSelector).each(function() {
        const buttonComponent = $(this).find('button');
        const isHtmlContent = buttonComponent[0].dataset.html === 'true';
        const canCopy = isHtmlContent && canUseClipboardWriteApi || !isHtmlContent && canUseClipboardWriteTextAPI;

        const tooltipTexts = canCopy ? tooltipTextsForCopy : tooltipTextsForSelection;

        buttonComponent.attr('data-original-title', tooltipTexts.initial).tooltip();

        const onSuccess = () => {
            buttonComponent.attr('data-original-title', tooltipTexts.success).tooltip('show');
            buttonComponent.attr('data-original-title', tooltipTexts.initial);
        }
        const onFailure = () => {
            buttonComponent.attr('data-original-title', tooltipTexts.failure).tooltip('show');
            buttonComponent.attr('data-original-title', tooltipTexts.initial);
        }

        const elementToCopy = $(this).find('.copy-to-clipboard-element');

        if (!elementToCopy.length) return;

        if (isHtmlContent && canUseClipboardWriteApi) {
            // Use the clipboard API to directly copy the desired html content
            buttonComponent.on('click', () => {
                const clipboardItem = new ClipboardItem({
                    "text/plain": new Blob(
                        [elementToCopy[0].innerText],
                        {type: "text/plain"}
                    ),
                    "text/html": new Blob(
                        [elementToCopy[0].outerHTML],
                        {type: "text/html"}
                    ),
                });
                navigator.clipboard.write([clipboardItem]).then(onSuccess, onFailure);

            });

        } else if (!isHtmlContent && canUseClipboardWriteTextAPI) {
            // Use the clipboard API to directly copy the desired text content
            buttonComponent.on('click', () => {
                navigator.clipboard.writeText(elementToCopy[0].innerText).then(onSuccess, onFailure);
            });
        }
        else {
            // Use the selection API to select the desired content
            buttonComponent.on('click', () => {
                const selection = window.getSelection();

                // Clear selection
                selection.removeAllRanges();

                // Select the content
                const range = document.createRange();
                range.selectNodeContents(elementToCopy[0]);
                selection.addRange(range);

                // Update the tooltip
                onSuccess();
            });
        }
    })
    $(clipboardSelector + ' button[data-toggle="tooltip"]').tooltip();
}
