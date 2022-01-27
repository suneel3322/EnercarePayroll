jQuery(function () {

    /**
     * Adding JS Chosen to Elements with Class name chosen-select
     */
    $('.chosen-select').chosen();


    /**
     * Track the page the user is currently on
     */
    $.ajax({
        url: "get-fns/big_brother.php",
        type: "POST",
        data: 'file=' + FILE + '' + '&csrfTokenName=' + TOKEN_NAME + '&csrfToken=' + TOKEN_VALUE + '&ajax=1',
        dataType: "html"
    });


    /**
     * Adding JS Tooltip to Elements with attribute data-toggle="tooltip"
     */
    $('[data-toggle="tooltip"]').tooltip({html: true});

    /**
     * Adding JS popovers to Elements with attribute data-toggle="popover"
     */
    $('[data-toggle="popover"]').popover();


    /**
     * Closing the Hopscotch Tour & Recording Action
     */
    $('.closeHopscotchMessage').click(function () {


        let id = $(this).attr('data-hopscotchId');
        let tokenName = $(this).attr("data-token-name");
        let tokenValue = $(this).attr("data-token");

        $.ajax({
            cache: false,
            type: "POST",
            url: "get-fns/tours/close_tour.php",
            data: {
                "hopSa": id,
                "csrfTokenName": tokenName,
                "csrfToken": tokenValue,
                "ajax": 1
            },
            success: function () {
                if (id == 2) {
                    $("#terms").fadeOut("slow");
                }
            }
        });
    });

    let count = 1;
    $('ol.breadcrumb').children('.breadcrumb-item').each(function () {
        $(this).attr('id', 'breadcrumb' + count);
        count++;
    });

});
