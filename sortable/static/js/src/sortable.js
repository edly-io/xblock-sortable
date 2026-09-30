/* Javascript for SortableXBlock. */
function SortableXBlock(runtime, element) {
    var $list = $(element).find('.items-list');
    var $live = $(element).find('.sortable-live');

    // jQuery UI's drop placeholder copies the row's classes while dragging.
    function getItems() {
        return $list.children('.item').not('.ui-sortable-placeholder');
    }

    function isLocked() {
        return $list.hasClass('is-locked');
    }

    function removeItemState() {
        getItems().removeClass('correct incorrect');
    }

    // `marks[i]` is 'correct' or 'incorrect' for the row at position i.
    function setItemsState(marks) {
        getItems().each(function(index) {
            var correct = marks[index] === 'correct';
            $(this).toggleClass('correct', correct).toggleClass('incorrect', !correct);
        });
    }

    function updateMoveButtons() {
        var $items = getItems();
        var last = $items.length - 1;
        var locked = isLocked();
        $items.each(function(index) {
            $(this).find('.move-up').prop('disabled', locked || index === 0);
            $(this).find('.move-down').prop('disabled', locked || index === last);
        });
    }

    function announcePosition($item) {
        var $items = getItems();
        // attr, not data: jQuery would try to parse a message starting with "{" as JSON.
        $live.text(
            String($live.attr('data-moved-message'))
                .replace('{position}', $items.index($item) + 1)
                .replace('{total}', $items.length)
        );
    }

    function onOrderChanged($item) {
        removeItemState();
        updateMoveButtons();
        announcePosition($item);
    }

    function moveItem($button, direction) {
        var $item = $button.closest('.item');
        var $neighbour = direction === 'up' ? $item.prev('.item') : $item.next('.item');
        if (isLocked() || !$neighbour.length) {
            return;
        }
        if (direction === 'up') {
            $item.insertBefore($neighbour);
        } else {
            $item.insertAfter($neighbour);
        }
        onOrderChanged($item);
        // Moving the row drops focus. Keep it on this row, on a button that
        // still works once the row reaches the top or bottom.
        if ($button.prop('disabled')) {
            $item.find(direction === 'up' ? '.move-down' : '.move-up').trigger('focus');
        } else {
            $button.trigger('focus');
        }
    }

    function lock() {
        $list.addClass('is-locked');
        if ($list.hasClass('ui-sortable')) {
            $list.sortable('disable');
        }
        updateMoveButtons();
    }

    // The exact item texts: the server matches them against its item list.
    function getItemsState() {
        return getItems().map(function() {
            return $(this).find('.item-text').text();
        }).get();
    }

    // jQuery UI leaves the dragged row at its old place in the DOM while it
    // is drawn elsewhere, so the CSS counter can't number it. Show the slot
    // it would land in instead.
    function showDragPosition(ui) {
        var slot = $list.children('.item').not(ui.item).index(ui.placeholder) + 1;
        ui.item.find('.item-position').attr('data-position', slot);
    }

    var handlerUrl = runtime.handlerUrl(element, 'submit_answer');

    $list.on('click', '.move-up', function() { moveItem($(this), 'up'); });
    $list.on('click', '.move-down', function() { moveItem($(this), 'down'); });

    $('#submit-answer', element).click(function(eventObject) {
        var $submit = $(this);
        // One request at a time: a double click must not use two attempts.
        $submit.prop('disabled', true);
        $.ajax({
            type: "POST",
            url: handlerUrl,
            data: JSON.stringify(getItemsState()),
            success: function(response) {
                var $notification = $(element).find('.notification.notification-submit');
                var $message = $(element).find('.notification.notification-submit .notification-message');
                var $icon = $(element).find('.notification.notification-submit .icon');
                var $attempts = $(element).find('.action .submission-feedback .attempts');
                var $errorIndicator = $(element).find('.indicator-container.error');
                var $successIndicator = $(element).find('.indicator-container.success');
                $message.html(response.message);
                $attempts.text(response.attempts);
                $notification.removeClass('is-hidden success error');
                if(response.correct) {
                    $notification.addClass('success');
                    $icon.removeClass('fa-close').addClass('fa-check');
                    $errorIndicator.addClass('is-hidden');
                    $successIndicator.removeClass('is-hidden');
                } else {
                    $notification.addClass('error');
                    $icon.removeClass('fa-check').addClass('fa-close');
                    $errorIndicator.removeClass('is-hidden');
                    $successIndicator.addClass('is-hidden');
                }
                setItemsState(response.marks);
                if(response.correct || response.remaining_attempts <= 0) {
                    lock();
                } else {
                    $submit.prop('disabled', false);
                }
            },
            error: function (request, status, error) {
                var $message = $(element).find('.submission-feedback .message');
                var errText = (request.responseJSON && request.responseJSON.error)
                    || 'Submission failed. Please try again.';
                $message.html(errText);
                $message.addClass('error');
                $message.show();
                setTimeout(function(){
                    $message.hide();
                    $message.removeClass('error');
                    $message.html('');
                    $submit.prop('disabled', isLocked());
                }, 4000);
            }
        });
    });

    if (!isLocked()) {
        $list.sortable({
            items: '> .item',
            start: function(event, ui) {
                ui.item.data('start_pos', ui.item.index());
                showDragPosition(ui);
            },
            change: function(event, ui) {
                showDragPosition(ui);
            },
            stop: function(event, ui) {
                ui.item.find('.item-position').removeAttr('data-position');
                if (ui.item.data('start_pos') != ui.item.index()) {
                    onOrderChanged(ui.item);
                }
            }
        });
    }
    updateMoveButtons();
}
