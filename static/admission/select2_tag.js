document.addEventListener('dal-init-function', function () {

    yl.registerFunction('select2_tag', function ($, element) {
        /*
         * We override the default select2 initialization:
         * - to prevent the overriding of the option value with the option label when the tags are used ("processResults" in the original file)
         * - to insert the tag option only if there is no other result ("insertTag" in this file)
         *
         * Note that to simplify the code, the part related to the creation of objects in Django has been removed.
         */
        const currentElement = $(element);

        function template(text, is_html) {
            if (is_html) {
                var $result = $('<span>');
                $result.html(text);
                return $result;
            } else {
                return text;
            }
        }

        function result_template(item) {
            return template(
                item.text,
                currentElement.attr('data-html') !== undefined || currentElement.attr('data-result-html') !== undefined
            );
        }

        function selected_template(item) {
            if (item.selected_text !== undefined) {
                return template(item.selected_text,
                    currentElement.attr('data-html') !== undefined || currentElement.attr('data-selected-html') !== undefined
                );
            } else {
                return result_template(item);
            }
        }

        var ajax = null;
        let ajaxResults = [];
        if (currentElement.attr('data-autocomplete-light-url')) {
            ajax = {
                url: currentElement.attr('data-autocomplete-light-url'),
                dataType: 'json',
                delay: 250,

                data: function (params) {
                    var data = {
                        q: params.term, // search term
                        page: params.page,
                        forward: yl.getForwards(currentElement)
                    };

                    return data;
                },
                processResults: function (data) {
                    // Store results ids to not create tag with similar ids, see createTag below.
                    ajaxResults = data.results.map(result => result.id);
                    return data;
                },
                cache: true
            };
        }
        let use_tags = false;
        let tokenSeparators = null;
        // Option 1: 'data-tags'
        if (currentElement.attr('data-tags')) {
            tokenSeparators = [','];
            use_tags = true;
        }
        // Option 2: 'data-token-separators'
        if (currentElement.attr('data-token-separators')) {
            use_tags = true
            tokenSeparators = currentElement.attr('data-token-separators')
            if (tokenSeparators === 'null') {
                tokenSeparators = null;
            }
        }
        currentElement.select2({
            tokenSeparators: tokenSeparators,
            debug: true,
            containerCssClass: ':all:',
            placeholder: currentElement.attr('data-placeholder') || '',
            language: currentElement.attr('data-autocomplete-light-language'),
            minimumInputLength: currentElement.attr('data-minimum-input-length') || 0,
            allowClear: !currentElement.is('[required]'),
            templateResult: result_template,
            templateSelection: selected_template,
            ajax: ajax,
            with: null,
            tags: use_tags,
            insertTag: function (data, tag) {
                // Insert the tag only if there is no result
                if (data.length === 0) {
                    data.push(tag);
                }
            },
            createTag: function (params) {
                // Do not create a tag if its value already exist in the list of result
                // https://github.com/select2/select2/issues/6091
                if (ajaxResults.includes(params.term)) {
                    return null;
                }
                return {
                    id: params.term,
                    text: params.term,
                }
            },
        });
    });
});
