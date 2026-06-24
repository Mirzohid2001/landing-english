/**
 * Mock test admin — savol turi bo'yicha maydonlarni ko'rsatish/yashirish.
 */
(function () {
    'use strict';

    var MCQ_TYPES = ['mcq', 'true_false_not_given', 'yes_no_not_given'];
    var FILL_TYPES = [
        'fill_blank',
        'sentence_completion',
        'summary_completion',
        'summary_box',
        'notes_completion',
        'table_completion',
    ];
    var MULTI_MATCHING = [
        'matching_headings',
        'matching_features',
        'matching_info',
        'matching_sentences',
        'classification',
    ];

    function showMcq(qType) {
        return qType && MCQ_TYPES.indexOf(qType) >= 0;
    }

    function showFillBlock(qType) {
        if (!qType) return false;
        return (
            FILL_TYPES.indexOf(qType) >= 0 ||
            qType === 'matching' ||
            MULTI_MATCHING.indexOf(qType) >= 0 ||
            qType === 'essay'
        );
    }

    function getInlineContainer(el) {
        if (!el) return null;
        return (
            el.closest('.inline-related') ||
            el.closest('.js-inline-admin-formset') ||
            el.closest('form')
        );
    }

    function getQuestionTypeSelect(container) {
        if (!container) return null;
        return container.querySelector('select[name$="-question_type"], select[name="question_type"]');
    }

    function toggleFieldset(fieldset, show) {
        if (!fieldset) return;
        fieldset.style.display = show ? '' : 'none';
        fieldset.classList.toggle('question-type-mcq-hidden', !show);
        fieldset.classList.toggle('question-type-section-visible', show);
        fieldset.setAttribute('aria-hidden', show ? 'false' : 'true');
    }

    function toggleFieldRow(container, fieldName, show) {
        if (!container) return;
        var fieldBox = container.querySelector('.field-box.field-' + fieldName);
        if (fieldBox) {
            fieldBox.style.display = show ? '' : 'none';
            fieldBox.classList.toggle('question-type-row-hidden', !show);
            var row = fieldBox.closest('.form-row');
            if (row) {
                var boxes = row.querySelectorAll(':scope > .field-box');
                var anyVisible = false;
                boxes.forEach(function (box) {
                    if (box.style.display !== 'none' && !box.classList.contains('question-type-row-hidden')) {
                        anyVisible = true;
                    }
                });
                row.style.display = anyVisible ? '' : 'none';
                row.classList.toggle('question-type-row-hidden', !anyVisible);
            }
            return;
        }
        var inp = container.querySelector('[name$="-' + fieldName + '"]');
        if (inp) {
            var inpRow = inp.closest('.form-row');
            if (inpRow) {
                inpRow.style.display = show ? '' : 'none';
                inpRow.classList.toggle('question-type-row-hidden', !show);
                return;
            }
        }
        var row = container.querySelector('.form-row.field-' + fieldName);
        if (row) {
            row.style.display = show ? '' : 'none';
            row.classList.toggle('question-type-row-hidden', !show);
        }
    }

    function toggleByField(container, fieldKey, show) {
        toggleFieldRow(container, fieldKey, show);
        container.querySelectorAll('[data-qt-field="' + fieldKey + '"]').forEach(function (inp) {
            var row = inp.closest('.form-row');
            if (row) {
                row.style.display = show ? '' : 'none';
                row.classList.toggle('question-type-row-hidden', !show);
            }
        });
    }

    function ensureShartDiv(container) {
        var select = getQuestionTypeSelect(container);
        if (!select || !window.QUESTION_TYPE_RULES) return null;
        var shartDiv = container.querySelector('.question-type-shart-box');
        if (!shartDiv) {
            shartDiv = document.createElement('div');
            shartDiv.className = 'question-type-shart-box';
            var row = select.closest('.form-row');
            if (row && row.parentNode) {
                row.parentNode.insertBefore(shartDiv, row.nextSibling);
            } else {
                container.appendChild(shartDiv);
            }
        }
        return shartDiv;
    }

    function updateShart(container, qType) {
        var shartDiv = ensureShartDiv(container);
        if (!shartDiv || !window.QUESTION_TYPE_RULES) return;
        var text = window.QUESTION_TYPE_RULES[qType] || '';
        if (text) {
            shartDiv.textContent = '\uD83D\uDCCB ' + text;
            shartDiv.style.display = 'block';
        } else {
            shartDiv.style.display = 'none';
        }
    }

    function hideUntilTypeChosen(container) {
        ['order', 'part_number', 'question_type', 'points'].forEach(function (name) {
            toggleFieldRow(container, name, true);
        });
        [
            'instruction',
            'question_text',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'correct_answer',
            'fill_answers',
            'matching_items',
            'matching_options_lines',
            'matching_correct',
            'word_list_lines',
            'correct_answer',
            'explanation',
            'audio_timestamp',
            'image',
            'correct_answers_json',
            'options_json',
        ].forEach(function (name) {
            toggleFieldRow(container, name, false);
        });
        container.querySelectorAll('fieldset.question-mcq-fields, fieldset.question-fill-fields').forEach(
            function (fs) {
                toggleFieldset(fs, false);
            }
        );
        var shart = container.querySelector('.question-type-shart-box');
        if (shart) shart.style.display = 'none';
    }

    function toggleByQuestionType(container) {
        if (!container) return;
        var select = getQuestionTypeSelect(container);
        if (!select) return;

        var qType = (select.value || '').trim();
        if (!qType) {
            hideUntilTypeChosen(container);
            return;
        }

        updateShart(container, qType);

        var showMcqFields = showMcq(qType);
        var showFill = showFillBlock(qType);
        var isMatching = qType === 'matching';
        var isMultiMatching = MULTI_MATCHING.indexOf(qType) >= 0;
        var isSummaryBox = qType === 'summary_box';
        var isFill =
            FILL_TYPES.indexOf(qType) >= 0 && qType !== 'summary_box';
        var isMcq = qType === 'mcq';
        var isTfng = qType === 'true_false_not_given' || qType === 'yes_no_not_given';
        var testType = getTestType();
        var showImage = testType === 'listening' && qType && qType !== 'essay';
        var isEssay = qType === 'essay';

        ['instruction', 'question_text', 'explanation', 'part_number', 'points'].forEach(
            function (name) {
                toggleFieldRow(container, name, true);
            }
        );
        var mcqFs = container.querySelector('fieldset.question-mcq-fields');
        var fillFs = container.querySelector('fieldset.question-fill-fields');
        container.classList.toggle('question-tfng-active', isTfng);
        container.classList.toggle('question-mcq-active', isMcq);
        toggleFieldset(mcqFs, showMcqFields);
        toggleFieldset(fillFs, showFill);

        if (isTfng) {
            ['option_a', 'option_b', 'option_c', 'correct_answer'].forEach(function (name) {
                toggleFieldRow(container, name, true);
            });
            ['option_d', 'option_e', 'option_f', 'option_g', 'option_h', 'mcq_select_count', 'mcq_options_lines'].forEach(function (name) {
                toggleFieldRow(container, name, false);
            });
        } else if (isMcq) {
            toggleFieldRow(container, 'option_a', true);
            toggleFieldRow(container, 'option_b', true);
            toggleFieldRow(container, 'option_c', true);
            toggleFieldRow(container, 'option_d', true);
            toggleFieldRow(container, 'option_e', true);
            toggleFieldRow(container, 'option_f', true);
            toggleFieldRow(container, 'option_g', true);
            toggleFieldRow(container, 'option_h', true);
            toggleFieldRow(container, 'mcq_select_count', true);
            toggleFieldRow(container, 'mcq_options_lines', true);
            toggleFieldRow(container, 'correct_answer', true);
        } else if (showMcqFields) {
            toggleFieldRow(container, 'option_a', true);
            toggleFieldRow(container, 'option_b', true);
            toggleFieldRow(container, 'option_c', false);
            toggleFieldRow(container, 'option_d', false);
            toggleFieldRow(container, 'option_e', false);
            toggleFieldRow(container, 'option_f', false);
            toggleFieldRow(container, 'option_g', false);
            toggleFieldRow(container, 'option_h', false);
            toggleFieldRow(container, 'mcq_select_count', false);
            toggleFieldRow(container, 'mcq_options_lines', false);
            toggleFieldRow(container, 'correct_answer', true);
        } else {
            ['option_a', 'option_b', 'option_c', 'option_d', 'option_e', 'option_f', 'option_g', 'option_h',
                'mcq_select_count', 'mcq_options_lines', 'correct_answer'].forEach(function (name) {
                toggleFieldRow(container, name, false);
            });
        }

        toggleFieldRow(container, 'fill_answers', isFill || isSummaryBox || qType === 'notes_completion' || qType === 'table_completion');
        toggleFieldRow(container, 'matching_items', isMultiMatching);
        toggleFieldRow(container, 'matching_options_lines', isMatching || isMultiMatching);
        toggleFieldRow(container, 'matching_correct', isMultiMatching);
        toggleFieldRow(container, 'word_list_lines', isSummaryBox);
        toggleFieldRow(container, 'audio_timestamp', !isEssay && testType === 'listening');
        toggleFieldRow(container, 'image', showImage);
        if (showImage) {
            ensureImageHint(container);
        }
        toggleFieldRow(
            container,
            'correct_answer',
            isTfng || isMcq || isMatching || (isFill && !isMultiMatching) || isSummaryBox
        );
        if (isMcq) {
            toggleFieldRow(container, 'correct_answer', true);
        }

        if (isEssay) {
            toggleFieldRow(container, 'fill_answers', false);
            toggleFieldRow(container, 'matching_items', false);
            toggleFieldRow(container, 'matching_options_lines', false);
            toggleFieldRow(container, 'matching_correct', false);
            toggleFieldRow(container, 'word_list_lines', false);
            toggleFieldRow(container, 'correct_answer', false);
            toggleFieldRow(container, 'audio_timestamp', false);
            toggleFieldRow(container, 'image', false);
        }
        if (isMultiMatching) {
            toggleFieldRow(container, 'correct_answer', false);
        }

        if (showMcqFields && qType === 'true_false_not_given') {
            autofillIfEmpty(container, 'option_a', 'True');
            autofillIfEmpty(container, 'option_b', 'False');
            autofillIfEmpty(container, 'option_c', 'Not Given');
        }
        if (showMcqFields && qType === 'yes_no_not_given') {
            autofillIfEmpty(container, 'option_a', 'Yes');
            autofillIfEmpty(container, 'option_b', 'No');
            autofillIfEmpty(container, 'option_c', 'Not Given');
        }

        toggleFieldRow(container, 'correct_answers_json', false);
        toggleFieldRow(container, 'options_json', false);
        updatePointsField(container);
        refreshRowCollapse(container);
    }

    function countBracketSlots(text) {
        var matches = (text || '').match(/\[\d+\]/g);
        return matches ? matches.length : 0;
    }

    function countCommaAnswers(text) {
        if (!text || !String(text).trim()) return 0;
        return String(text).replace(/\n/g, ',').split(',').filter(function (s) {
            return s.trim();
        }).length;
    }

    function estimateGradableSlots(container) {
        var qType = fieldValue(container, 'question_type') || '';
        var qtext = fieldValue(container, 'question_text') || '';
        var fill = fieldValue(container, 'fill_answers') || '';
        var brackets = countBracketSlots(qtext);

        if (qType === 'mcq') {
            var selectCount = parseInt(fieldValue(container, 'mcq_select_count') || '1', 10);
            if (isNaN(selectCount) || selectCount < 1) selectCount = 1;
            if (selectCount > 3) selectCount = 3;
            return selectCount;
        }

        if (
            qType === 'summary_box' ||
            qType === 'notes_completion' ||
            qType === 'table_completion' ||
            qType === 'fill_blank' ||
            qType === 'sentence_completion' ||
            qType === 'summary_completion'
        ) {
            if (brackets) return brackets;
            return 1;
        }
        if (MULTI_MATCHING.indexOf(qType) >= 0) {
            var corr = fieldValue(container, 'matching_correct') || '';
            var corrLines = corr.split('\n').filter(function (l) { return l.trim(); });
            if (corrLines.length) return corrLines.length;
            var items = fieldValue(container, 'matching_items') || '';
            var itemLines = items.split('\n').filter(function (l) { return l.trim(); });
            return itemLines.length || 1;
        }
        return 1;
    }

    function ensurePointsHint(container, slots) {
        var row = container.querySelector('.form-row.field-points');
        if (!row) return;
        var hint = row.querySelector('.mock-points-slot-hint');
        if (!hint) {
            hint = document.createElement('p');
            hint.className = 'mock-points-slot-hint help';
            row.appendChild(hint);
        }
        if (slots > 1) {
            hint.textContent =
                'Baholanadigan slotlar: ' + slots +
                ' — ball saqlashda avtomatik shu songa tenglashtiriladi';
        } else {
            hint.textContent = '1 ta slot.';
        }
    }

    function updatePointsField(container) {
        if (!container) return;
        var pointsInp = container.querySelector('[name$="-points"]');
        if (!pointsInp) return;
        var slots = estimateGradableSlots(container);
        if (slots < 1) slots = 1;
        ensurePointsHint(container, slots);
        if (slots > 1) {
            pointsInp.value = String(slots);
            pointsInp.readOnly = true;
            pointsInp.classList.add('mock-points-auto');
        } else {
            pointsInp.readOnly = false;
            pointsInp.classList.remove('mock-points-auto');
            if (!pointsInp.value || parseInt(pointsInp.value, 10) < 1) pointsInp.value = '1';
        }
    }

    function autofillIfEmpty(container, field, value) {
        var el = container.querySelector('[name$="-' + field + '"]');
        if (el && !String(el.value || '').trim()) el.value = value;
    }

    function ensureImageHint(container) {
        if (!container || container.querySelector('.mock-image-hint')) return;
        var row = container.querySelector('.form-row.field-image');
        if (!row) return;
        var hint = document.createElement('p');
        hint.className = 'mock-image-hint';
        hint.textContent =
            'Xarita/jadval uchun bitta rasm yetadi — shu blokdagi birinchi savolga yuklang, testda bir marta ko\'rinadi.';
        row.appendChild(hint);
    }

    function bindImagePreview(container) {
        if (!container) return;
        var input = container.querySelector('input[type="file"][name$="-image"], input[type="file"][name="image"]');
        if (!input || input.dataset.mockImgPreviewBound) return;
        input.dataset.mockImgPreviewBound = '1';
        input.addEventListener('change', function () {
            var row = input.closest('.form-row.field-image');
            if (!row) return;
            var old = row.querySelector('.mock-admin-image-preview');
            if (old) old.remove();
            var file = input.files && input.files[0];
            if (!file || !file.type.match(/^image\//)) return;
            var img = document.createElement('img');
            img.className = 'mock-admin-image-preview';
            img.alt = 'Tanlangan rasm';
            img.src = URL.createObjectURL(file);
            row.appendChild(img);
        });
    }

    function initQuestionForm(container) {
        if (!container) return;
        var select = getQuestionTypeSelect(container);
        if (!select) return;

        if (!select.dataset.mockQtBound) {
            select.dataset.mockQtBound = '1';
            select.addEventListener('change', function () {
                toggleByQuestionType(container);
            });
        }
        toggleByQuestionType(container);
        bindImagePreview(container);
    }

    function runInit() {
        initAll();
        setTimeout(initAll, 100);
        setTimeout(initAll, 400);
        setTimeout(initAll, 1000);
    }

    document.addEventListener(
        'change',
        function (e) {
            if (
                e.target &&
                e.target.matches &&
                e.target.matches('select[name$="-question_type"], select[name="question_type"]')
            ) {
                var container = getInlineContainer(e.target);
                toggleByQuestionType(container);
            }
        },
        true
    );

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runInit);
        window.addEventListener('load', runInit);
    } else {
        runInit();
    }

    var QUICK_TEMPLATES = {
        mcq: {
            question_type: 'mcq',
            mcq_select_count: 1,
            question_text: 'Choose the correct answer.',
            option_a: 'Option A',
            option_b: 'Option B',
            option_c: 'Option C',
            option_d: 'Option D',
            correct_answer: 'b',
        },
        mcq_multi: {
            question_type: 'mcq',
            mcq_select_count: 2,
            question_text: 'Choose TWO correct answers.',
            option_a: 'First answer',
            option_b: 'Second answer',
            option_c: 'Third answer',
            option_d: 'Fourth answer',
            option_e: 'Fifth answer',
            correct_answer: 'a,c',
        },
        notes: {
            question_type: 'notes_completion',
            question_text: 'Name [1], from [2]',
            fill_answers: 'anna, london',
        },
        tfng: {
            question_type: 'true_false_not_given',
            question_text: 'Statement about the text.',
            option_a: 'True',
            option_b: 'False',
            option_c: 'Not Given',
            correct_answer: 'c',
        },
        ynng: {
            question_type: 'yes_no_not_given',
            question_text: 'Statement about the text.',
            option_a: 'Yes',
            option_b: 'No',
            option_c: 'Not Given',
            correct_answer: 'c',
        },
        fill: {
            question_type: 'fill_blank',
            question_text: 'Complete: The city is called ______.',
            fill_answers: 'london',
            correct_answer: 'london',
        },
        matching_h: {
            question_type: 'matching_headings',
            question_text: 'Match headings to paragraphs.',
            matching_items: '14|Paragraph A\n15|Paragraph B',
            matching_options_lines: 'i|First heading\nii|Second heading\niii|Third heading',
            matching_correct: '14:i\n15:ii',
        },
        summary_box: {
            question_type: 'summary_box',
            question_text: (
                'How to use City Cycle\n'
                '-- Select a bike by using the [11]\n'
                '-- Release the bike by using the [12] of your chosen bike.'
            ),
            fill_answers: 'button, website',
            word_list_lines: 'button\nwebsite\nhelmet',
        },
    };

    function getTestType() {
        if (window.MOCK_TEST_META && window.MOCK_TEST_META.type) {
            return window.MOCK_TEST_META.type;
        }
        if (window.MOCK_QUESTION_TEST_TYPE) {
            return window.MOCK_QUESTION_TEST_TYPE;
        }
        var el = document.getElementById('id_test_type');
        return el && el.value ? el.value : 'reading';
    }

    function partFromOrder(order, testType) {
        var n = parseInt(order, 10);
        if (!n || isNaN(n)) return 1;
        if (testType === 'listening') {
            if (n <= 10) return 1;
            if (n <= 20) return 2;
            if (n <= 30) return 3;
            return 4;
        }
        if (testType === 'reading') {
            if (n <= 13) return 1;
            if (n <= 26) return 2;
            return 3;
        }
        if (testType === 'writing') {
            return n <= 1 ? 1 : 2;
        }
        return 1;
    }

    function defaultQuestionType(testType) {
        if (testType === 'listening') return 'notes_completion';
        if (testType === 'writing') return 'essay';
        return 'mcq';
    }

    function getMaxOrder(excludeInput) {
        var max = 0;
        document.querySelectorAll('input[name$="-order"]').forEach(function (inp) {
            if (excludeInput && inp === excludeInput) return;
            var v = parseInt(inp.value, 10);
            if (!isNaN(v) && v > max) max = v;
        });
        return max;
    }

    function suggestRowDefaults(container, force) {
        if (!container) return;
        var orderInp = container.querySelector('input[name$="-order"]');
        var partInp = container.querySelector('input[name$="-part_number"]');
        var typeSelect = getQuestionTypeSelect(container);
        var deleteCheck = container.querySelector('input[name$="-DELETE"]');
        if (deleteCheck && deleteCheck.checked) return;

        var testType = getTestType();
        if (orderInp && (force || !orderInp.value)) {
            orderInp.value = getMaxOrder(orderInp) + 1;
        }
        var orderVal = orderInp ? parseInt(orderInp.value, 10) : 0;
        if (partInp && (force || !partInp.value) && orderVal) {
            partInp.value = partFromOrder(orderVal, testType);
        }
        if (typeSelect && (force || !typeSelect.value)) {
            typeSelect.value = defaultQuestionType(testType);
            typeSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    function getQuestionGroup() {
        return document.getElementById('questions-group') || document.getElementById('mockquestion_set-group');
    }

    function getInlineRows() {
        var group = getQuestionGroup();
        var root = group ? group.querySelectorAll('.inline-related') : document.querySelectorAll('#content-main .inline-related');
        return Array.prototype.slice.call(root).filter(function (row) {
            return getQuestionTypeSelect(row);
        });
    }

    function findPreviousRow(container) {
        var rows = getInlineRows();
        var idx = rows.indexOf(container);
        if (idx > 0) return rows[idx - 1];
        return null;
    }

    function fieldValue(row, suffix) {
        var el = row.querySelector('[name$="-' + suffix + '"]');
        if (!el) return '';
        if (el.type === 'checkbox') return el.checked;
        return el.value;
    }

    function setFieldValue(row, suffix, value) {
        var el = row.querySelector('[name$="-' + suffix + '"]');
        if (!el) return;
        if (el.type === 'checkbox') {
            el.checked = !!value;
        } else {
            el.value = value;
        }
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function duplicateFromPrevious(container) {
        var prev = findPreviousRow(container);
        if (!prev) {
            window.alert('Oldingi savol yo\'q — avval bir savol qo\'shing.');
            return;
        }
        var testType = getTestType();
        var nextOrder = getMaxOrder(container.querySelector('input[name$="-order"]')) + 1;
        var copyFields = [
            'question_type', 'part_number', 'points', 'instruction',
            'option_a', 'option_b', 'option_c', 'option_d',
            'option_e', 'option_f', 'option_g', 'option_h',
            'mcq_select_count', 'mcq_options_lines',
            'fill_answers', 'matching_items', 'matching_options_lines',
            'matching_correct', 'word_list_lines', 'explanation', 'audio_timestamp',
        ];
        copyFields.forEach(function (name) {
            setFieldValue(container, name, fieldValue(prev, name));
        });
        setFieldValue(container, 'order', nextOrder);
        setFieldValue(container, 'part_number', partFromOrder(nextOrder, testType));
        setFieldValue(container, 'question_text', '');
        setFieldValue(container, 'correct_answer', '');
        var typeSelect = getQuestionTypeSelect(container);
        if (typeSelect) toggleByQuestionType(container);
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function isSavedInlineRow(container) {
        var idInp = container.querySelector('input[name$="-id"]');
        return !!(idInp && idInp.value);
    }

    function addDeleteHelper(container, tools) {
        if (!isSavedInlineRow(container) || container.querySelector('.mock-delete-helper')) return;
        var delCheck = container.querySelector('input[name$="-DELETE"]');
        if (!delCheck) return;

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'mock-delete-helper button';
        btn.textContent = 'O\'chirish';
        btn.addEventListener('click', function () {
            delCheck.checked = !delCheck.checked;
            container.classList.toggle('mock-row-marked-delete', delCheck.checked);
            btn.classList.toggle('is-active', delCheck.checked);
            btn.textContent = delCheck.checked ? 'O\'chirish bekor' : 'O\'chirish';
            updateQuestionStats();
        });
        delCheck.addEventListener('change', function () {
            container.classList.toggle('mock-row-marked-delete', delCheck.checked);
            btn.classList.toggle('is-active', delCheck.checked);
            btn.textContent = delCheck.checked ? 'O\'chirish bekor' : 'O\'chirish';
            updateQuestionStats();
        });
        tools.appendChild(btn);
    }

    function isBlankInlineRow(container) {
        if (isSavedInlineRow(container)) return false;
        var text = fieldValue(container, 'question_text');
        var answers = fieldValue(container, 'fill_answers') || fieldValue(container, 'correct_answer');
        return !String(text || '').trim() && !String(answers || '').trim();
    }

    function addRemoveEmptyHelper(container, tools) {
        if (!isBlankInlineRow(container) || container.querySelector('.mock-remove-empty-btn')) return;
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'mock-remove-empty-btn button';
        btn.textContent = 'Bo\'sh qatorni olib tashlash';
        btn.addEventListener('click', function () {
            var delCheck = container.querySelector('input[name$="-DELETE"]');
            if (delCheck) {
                delCheck.checked = true;
                container.style.display = 'none';
            } else {
                container.remove();
                var total = document.querySelector('input[name$="-TOTAL_FORMS"]');
                if (total) {
                    var rows = getInlineRows().filter(function (row) {
                        return row.parentNode && row.style.display !== 'none';
                    });
                    total.value = String(rows.length);
                }
            }
            updateQuestionStats();
        });
        tools.appendChild(btn);
    }

    function addInlineTools(container) {
        if (!container || container.querySelector('.mock-inline-tools')) return;
        var tools = document.createElement('div');
        tools.className = 'mock-inline-tools';

        var dupBtn = document.createElement('button');
        dupBtn.type = 'button';
        dupBtn.className = 'mock-dup-prev-btn button';
        dupBtn.textContent = 'Oldingisidan nusxa';
        dupBtn.addEventListener('click', function () {
            duplicateFromPrevious(container);
        });

        var suggestBtn = document.createElement('button');
        suggestBtn.type = 'button';
        suggestBtn.className = 'mock-suggest-order-btn button';
        suggestBtn.textContent = 'Order/Part avto';
        suggestBtn.addEventListener('click', function () {
            suggestRowDefaults(container, true);
        });

        tools.appendChild(dupBtn);
        tools.appendChild(suggestBtn);
        addDeleteHelper(container, tools);
        addRemoveEmptyHelper(container, tools);

        var anchor = container.querySelector('h3') || container.querySelector('.inline_label') || container.firstElementChild;
        if (anchor && anchor.parentNode) {
            anchor.parentNode.insertBefore(tools, anchor.nextSibling);
        } else {
            container.insertBefore(tools, container.firstChild);
        }
    }

    function updateQuestionStats() {
        var statsEl = document.getElementById('mock-admin-question-stats');
        var slotEl = document.getElementById('mock-admin-slot-stats');
        if (!statsEl) return;
        var rows = getInlineRows();
        var parts = {};
        var count = 0;
        var totalSlots = 0;
        var totalPoints = 0;
        var mismatches = 0;
        rows.forEach(function (row) {
            var del = row.querySelector('input[name$="-DELETE"]');
            if (del && del.checked) return;
            var order = fieldValue(row, 'order');
            if (!order) return;
            count += 1;
            var part = fieldValue(row, 'part_number') || '?';
            parts[part] = (parts[part] || 0) + 1;
            var slots = estimateGradableSlots(row);
            totalSlots += slots;
            var pts = parseInt(fieldValue(row, 'points') || '0', 10);
            if (!isNaN(pts)) totalPoints += pts;
            if (pts > 0 && pts !== slots) mismatches += 1;
        });
        if (!count) {
            statsEl.textContent = 'Hali savol qatorlari bo\'sh — «Yana bir Savol qo\'shish» bosing.';
            if (slotEl) slotEl.textContent = '';
            return;
        }
        var partText = Object.keys(parts).sort().map(function (p) {
            return 'Part ' + p + ': ' + parts[p] + ' ta qator';
        }).join(' · ');
        statsEl.textContent = 'Jami ' + count + ' ta savol qatori · ' + partText;
        if (slotEl) {
            var slotLine =
                'Baholanadigan slotlar: ' + totalSlots +
                ' · Jami ball (form): ' + totalPoints;
            if (mismatches) {
                slotLine += ' · ⚠ ' + mismatches + ' ta qatorda ball ≠ slot (Saqlash tuzatadi)';
            }
            if (window.MOCK_TEST_SAVED_STATS && !mismatches) {
                var saved = window.MOCK_TEST_SAVED_STATS;
                if (saved.gradable_slots !== totalSlots || saved.total_points !== totalPoints) {
                    slotLine += ' · Saqlanmagan o\'zgarishlar bor';
                }
            }
            slotEl.textContent = slotLine;
        }
    }

    function applyTemplateToRow(container, templateKey) {
        var tpl = QUICK_TEMPLATES[templateKey];
        if (!tpl || !container) return;
        Object.keys(tpl).forEach(function (key) {
            setFieldValue(container, key, tpl[key]);
        });
        suggestRowDefaults(container, true);
        var typeSelect = getQuestionTypeSelect(container);
        if (typeSelect) toggleByQuestionType(container);
        container.classList.add('mock-inline-expanded');
        container.classList.remove('mock-inline-collapsed');
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
        var qt = container.querySelector('[name$="-question_text"]');
        if (qt) qt.focus();
    }

    function clickAddQuestion() {
        var group = getQuestionGroup();
        var link = group ? group.querySelector('.add-row a') : null;
        if (!link) {
            link = document.querySelector('#mockquestion_set-group .add-row a');
        }
        if (link) link.click();
    }

    function addFromTemplate(templateKey) {
        clickAddQuestion();
        setTimeout(function () {
            var rows = getInlineRows();
            var row = rows[rows.length - 1];
            if (row) applyTemplateToRow(row, templateKey);
            updateQuestionStats();
        }, 220);
    }

    function rowSummaryText(row) {
        var order = fieldValue(row, 'order') || '?';
        var qtype = fieldValue(row, 'question_type') || 'tur tanlanmagan';
        var slots = estimateGradableSlots(row);
        var text = fieldValue(row, 'question_text') || '';
        text = text.replace(/\s+/g, ' ').trim();
        if (text.length > 48) text = text.slice(0, 48) + '…';
        return '#' + order + ' · ' + qtype + ' · ' + slots + ' slot' + (text ? ' — ' + text : '');
    }

    function refreshRowCollapse(row) {
        if (!row) return;
        var idInp = row.querySelector('input[name$="-id"]');
        var isSaved = idInp && idInp.value;
        var summary = row.querySelector('.mock-row-summary');
        if (!summary) {
            summary = document.createElement('button');
            summary.type = 'button';
            summary.className = 'mock-row-summary';
            row.insertBefore(summary, row.firstChild);
            summary.addEventListener('click', function () {
                row.classList.toggle('mock-inline-expanded');
                row.classList.toggle('mock-inline-collapsed');
            });
        }
        summary.textContent = rowSummaryText(row) + '  ▾ ochish';
        if (isSaved && !row.classList.contains('mock-inline-expanded')) {
            row.classList.add('mock-inline-collapsed');
        }
        if (!isSaved) {
            row.classList.add('mock-inline-expanded');
            row.classList.remove('mock-inline-collapsed');
        }
    }

    function collapseAllSaved() {
        getInlineRows().forEach(function (row) {
            var idInp = row.querySelector('input[name$="-id"]');
            if (idInp && idInp.value) {
                row.classList.add('mock-inline-collapsed');
                row.classList.remove('mock-inline-expanded');
            }
        });
    }

    function expandAllRows() {
        getInlineRows().forEach(function (row) {
            row.classList.add('mock-inline-expanded');
            row.classList.remove('mock-inline-collapsed');
        });
    }

    function injectQuickToolbar() {
        var group = getQuestionGroup();
        if (!group || group.querySelector('.mock-quick-toolbar')) return;

        var bar = document.createElement('div');
        bar.className = 'mock-quick-toolbar';
        bar.innerHTML =
            '<span class="mock-quick-label">Tez qo\'shish:</span>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="mcq">+ MCQ</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="mcq_multi">+ MCQ (2 javob)</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="notes">+ Notes</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="tfng">+ T/F/NG</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="ynng">+ Y/N/NG</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="fill">+ Bo\'sh joy</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="matching_h">+ Headings</button>' +
            '<span class="mock-quick-spacer"></span>' +
            '<button type="button" class="button mock-collapse-btn" id="mock-collapse-all">Yig\'ish</button>' +
            '<button type="button" class="button mock-collapse-btn" id="mock-expand-all">Hammasini ochish</button>';

        group.insertBefore(bar, group.firstChild);

        bar.querySelectorAll('.mock-tpl-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                addFromTemplate(btn.getAttribute('data-tpl'));
            });
        });
        bar.querySelector('#mock-collapse-all').addEventListener('click', collapseAllSaved);
        bar.querySelector('#mock-expand-all').addEventListener('click', expandAllRows);
    }

    function injectListeningAudio() {
        var meta = window.MOCK_TEST_META;
        if (!meta || meta.type !== 'listening' || !meta.audioUrl) return;
        var group = getQuestionGroup();
        if (!group || group.querySelector('.mock-admin-audio-bar')) return;

        var wrap = document.createElement('div');
        wrap.className = 'mock-admin-audio-bar';
        wrap.innerHTML =
            '<strong>Listening audio</strong>' +
            '<audio controls preload="metadata" class="mock-admin-audio-el" src="' + meta.audioUrl + '"></audio>' +
            '<span class="mock-admin-audio-tip">Audio vaqtini (soniya) tinglab yozing — har savolda «Audio vaqti» maydoni.</span>';
        var toolbar = group.querySelector('.mock-quick-toolbar');
        if (toolbar) {
            group.insertBefore(wrap, toolbar.nextSibling);
        } else {
            group.insertBefore(wrap, group.firstChild);
        }
    }

    function enhanceInlineRow(container, autoDefaults) {
        initQuestionForm(container);
        addInlineTools(container);
        if (autoDefaults) suggestRowDefaults(container, true);
        refreshRowCollapse(container);
    }

    function initAll() {
        injectQuickToolbar();
        injectListeningAudio();
        var group = getQuestionGroup();
        var inlineSelector = group
            ? '#questions-group .inline-related, #mockquestion_set-group .inline-related'
            : '#content-main .inline-related';
        document.querySelectorAll(inlineSelector).forEach(function (el) {
            if (el.querySelector('select[name$="-question_type"], select[name="question_type"]')) {
                enhanceInlineRow(el, false);
            }
        });
        var qForm = document.getElementById('mockquestion_form');
        if (qForm) initQuestionForm(qForm);
        updateQuestionStats();
    }

    document.addEventListener('change', function (e) {
        if (e.target && e.target.id === 'id_test_type') {
            document.querySelectorAll('#questions-group .inline-related, #mockquestion_set-group .inline-related, #mockquestion_form').forEach(function (el) {
                if (getQuestionTypeSelect(el) || el.id === 'mockquestion_form') {
                    toggleByQuestionType(el);
                }
            });
        }
    });

    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('formset:added', function (event, $row, name) {
            if (String(name).indexOf('question') >= 0 && $row && $row[0]) {
                enhanceInlineRow($row[0], true);
            }
        });
    }

    document.addEventListener('input', function (e) {
        if (!e.target || !e.target.matches) return;
        if (e.target.matches(
            'input[name$="-order"], input[name$="-part_number"], textarea[name$="-question_text"], ' +
            'input[name$="-fill_answers"], textarea[name$="-matching_items"], textarea[name$="-matching_correct"], ' +
            'select[name$="-mcq_select_count"], input[name$="-points"]'
        )) {
            updateQuestionStats();
            var row = getInlineContainer(e.target);
            if (row) {
                refreshRowCollapse(row);
                updatePointsField(row);
            }
        }
    });

    document.addEventListener('change', function (e) {
        if (!e.target || !e.target.matches) return;
        if (e.target.matches('select[name$="-question_type"]')) {
            var row = getInlineContainer(e.target);
            if (row) updatePointsField(row);
        }
    });

    if (window.MutationObserver) {
        var timer;
        var group = getQuestionGroup();
        if (group) {
            new MutationObserver(function () {
                clearTimeout(timer);
                timer = setTimeout(initAll, 150);
            }).observe(group, { childList: true, subtree: true });
        }
    }
})();
