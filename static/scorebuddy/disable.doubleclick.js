jQuery(function () {

    $(".disable-doubleclick").on('click', function () {
        let button = $(this);
        disableDoubleClick(button)
    });

    $("#modal-popup").on('click', ".disable-doubleclick", function () {
        let button = $(this);
        disableDoubleClick(button)
    });


    function disableDoubleClick(button) {

        button.prop('disabled', true);

        if (!button.hasClass('disable-doubleclick-no-submit')) {
            button.parents('form:first').submit();
        }

        let button_timeout = 3000;
        if (button.hasClass('disable-doubleclick-15')) {
            button_timeout = 15000;
        }

        setTimeout(function () {
            button.prop('disabled', false);
        }, button_timeout);

    }

});
