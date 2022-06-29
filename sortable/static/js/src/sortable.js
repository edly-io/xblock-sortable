/* Javascript for SortableXBlock. */
function SortableXBlock(runtime, element) {

    function removeItemState() {
        $('.item', element).each(function(index){
            $(this).removeClass('incorrect');
        });
    }

    function setItemsState(state) {
        $('.item', element).each(function(index){
            if (index != state[index]){
                $(this).addClass('incorrect');
            }
        });
    }

    function getItemsState(result) {
        var data = []
        $('.item', element).each(function(){
            data.push($(this).text().trim());
        });

        return data
    }

    var handlerUrl = runtime.handlerUrl(element, 'submit_answer');

    $('#submit-answer', element).click(function(eventObject) {
        $.ajax({
            type: "POST",
            url: handlerUrl,
            data: JSON.stringify(getItemsState()),
            success: function(response) {
                var $notification = $(element).find('.notification.notification-submit');
                var $message = $(element).find('.notification.notification-submit .notification-message');
                var $icon = $(element).find('.notification.notification-submit .icon');
                var $attemptsInfo = $(element).find('.action .submission-feedback .attempts-info');
                var $errorIndicator = $(element).find('.indicator-container.error');
                var $successIndicator = $(element).find('.indicator-container.success');
                var $problemProgress = $(element).find('.problem-progress');
                $message.html(response.message);
                $attemptsInfo.html(response.attempts_info);
                $problemProgress.html(response.progress_info);
                $notification.removeClass('is-hidden');
                if(response.correct) {
                    $notification.addClass('success');
                    $icon.removeClass('fa-close');
                    $icon.addClass('fa-check');
                    $errorIndicator.addClass('is-hidden');
                    $successIndicator.removeClass('is-hidden');
                    $(element).find('#submit-answer').prop('disabled', true);
                } else {
                    $notification.addClass('error');
                    $icon.addClass('fa-close');
                    $errorIndicator.removeClass('is-hidden');
                    $successIndicator.addClass('is-hidden');
                    setItemsState(response.state);
                }
                if(response.remaining_attempts == 0) {
                    $(element).find('#submit-answer').prop('disabled', true);
                    $(element).find('.items-list').sortable('disable')
                }
            },
            error: function (request, status, error) {
                var $message = $(element).find('.feedback .message');
                $message.html(request.responseJSON.error);
                $message.addClass('error');
                $message.show();
                $(element).find('#submit-answer').prop('disabled', true);
                setTimeout(function(){ 
                    $message.hide();
                    $message.removeClass('error');
                    $message.html('');
                }, 4000);
            }
        });
    });

    is_button_disabled = $(element).find('#submit-answer').is(":disabled");

    if (!is_button_disabled) {
        $(element).find('.items-list').sortable(
            {
                start: function(event, ui) {
                    ui.item.data('start_pos', ui.item.index());
                },
                stop: function(event, ui) {
                    var start_pos = ui.item.data('start_pos');
                    if (start_pos != ui.item.index()) {
                        removeItemState()
                    } else {
                        // the item was returned to the same position
                    }
                }
            }
        );
    }
}
