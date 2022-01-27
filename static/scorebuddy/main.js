/**
 * @author Dave Sherlock
 * @description Confirmation Dialog Box using Modal. Needs to be placed outside of the document ready.
 * @param title
 * @param message
 * @param button_txt
 * @param confirm_type
 * @param handler
 */
function confirmDialog(title, message, button_txt = '', confirm_type, handler) {

    if (button_txt == '') {
        button_txt = 'Yes';
    }


    let content = '<div class="modal-content">\n' +
        '    <div class="modal-header">\n' +
        '        <h3 class="modal-title">' + title + '</h3>\n' +
        '        <button type="button" class="close" data-dismiss="modal" aria-label="Close">\n' +
        '            <span aria-hidden="true">×</span>\n' +
        '        </button>\n' +
        '    </div>\n' +
        '        <div class="modal-body p-4">\n' +
        '            <p>\n' + message + '</p>\n' +
        '        <div class="text-center"> <div class="ajax_loader" role="status"> <span class="sr-only">Loading...</span> </div> </div>' +
        '    </div>\n' +
        '    <div class="modal-footer">\n' +
        '       <button type="button" class="btn round btn-secondary btn-no" data-dismiss="modal">No</button>\n' +
        '       <button type="button" class="btn round btn-' + confirm_type + ' btn-yes" data-dismiss="modal">' + button_txt + '</button>\n' +
        '    </div>\n' +
        '</div>';


    //load in the content
    $('#modal-popup').modal({
        backdrop: 'static',
        keyboard: false
    }).find('.modal-content').html(content);


    //Pass true to a callback function
    $(".btn-yes").click(function () {
        $('.ajax_loader').show();
        handler(true);
        $("#modal-popup").modal("hide");
    });

    //Pass false to callback function
    $(".btn-no").click(function () {
        $('.ajax_loader').hide();
        handler(false);
        $("#modal-popup").modal("hide");
    });

    //Closing the popup is the same as saying no
    $("#modal-popup").on('hidden.bs.modal', function () {
        $('.ajax_loader').hide();
        handler(false);
        $("#modal-popup").modal("hide");
    });

}

/**
 * Basic Check for all required inputs.
 */
function checkRequired() {

    $('.parsley-errors-list').remove();

    let formFail = false;
    $('input,textarea,select').filter('[required]:visible').each(function () {
        //checks for empty strings and empty objects


        if ($(this).val() === null || (typeof $(this).val() === 'string' && !$(this).val().trim()) || $(this).val().length === 0 || (parseInt($(this).val()) < 0 && $(this).val() !== '-1')) {
            $(this).removeClass('parsley-success').addClass('validation-listener').addClass('parsley-error');
            $(this).parent().append("<ul class='parsley-errors-list'><li class=\"parsley-required\">This value is required.</li></ul>");
            $('.parsley-errors-list').css('opacity', '1');
            formFail = true;
        } else {
            $(this).removeClass('parsley-error').addClass('parsley-success');
        }
    });

    /*
    Special Required Check for Js Chosen Inputs
     */
    $('.chosen-select').filter('[required]').each(function () {
        //checks for empty objects but only ones that are visible non the page
        if ($(this).val().length === 0 && $(this).next('.chosen-container-multi').children('.chosen-choices').is(":visible")) {
            $(this).next('.chosen-container-multi').children('.chosen-choices').removeClass('parsley-success').addClass('parsley-error');
            $(this).addClass('validation-listener');
            $(this).parent().append("<ul class='parsley-errors-list'><li class=\"parsley-required\">This value is required.</li></ul>");
            $('.parsley-errors-list').css('opacity', '1');
            formFail = true;
        } else {
            $(this).next('.chosen-container-multi').children('.chosen-choices').removeClass('parsley-error').addClass('parsley-success');
        }
    });

    return formFail;
}

/**
 * Add a listener for invalid inputs so they can be re-checked on change
 */
$(document).on('change', 'form .validation-listener', function () {
    checkRequired();
});


/**
 * @description Standard Response to Ajax Requests
 * @param response
 * @param message
 * @param button
 * @param reload
 */
function successResponse(response, message, button = '', reload = true, parse = true) {

    let data = (parse === true) ? JSON.parse(response) : response;

    if (data.error === "csrf_failed" && document.location.href.match(/[^\/]+$/)[0] !== 'error.php') {
        alertify.error('CSRF Failed: CSRF token missing or incorrect.');
    }

    if (data.success) {
        alertify.success(message);
        if (reload) {
            setTimeout(function () {
                window.location.reload();
            }, 1000);
        }
    } else if (data.errorInfo) {
        alertify.error(data.errorInfo);
    }

    if (button) {
        button.attr("data-token-name", data.csrfTokenName);
        button.attr("data-token", data.csrfToken);
        button.removeClass('disabled');
    }

    return data;
}

/**
 * Configuration for a large data table
 * @type {{dom: string, pageLength: number, ordering: boolean, bInfo: boolean, pagingType: string, paging: boolean, language: {searchPlaceholder: string, search: string, emptyTable: string, lengthMenu: string}, info: boolean}}
 */
let LARGE_TABLE = {
    paging: true,
    pageLength: 100,
    pagingType: 'simple',
    ordering: false,
    info: false,
    dom: "<'row'<'col-sm-12 col-md-6 float-left'f><'col-sm-12 col-md-6'l>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
    bInfo: true,
    language: {
        emptyTable: "No Data found",
        search: "",
        searchPlaceholder: "Search...",
        lengthMenu: 'View ' +
            '<select class="custom-select custom-select-sm form-control form-control-sm">' +
            '<option value="100">100</option>' +
            '<option value="500">500</option>' +
            '<option value="1000">1000</option>' +
            '<option value="5000">5000</option>' +
            '<option value="-1">All</option>' +
            '</select>',
    }
};

/**
 * Configuration for a small data table
 * @type {{dom: string, ordering: boolean, paging: boolean, language: {searchPlaceholder: string, search: string, emptyTable: string}, info: boolean}}
 */
let SMALL_TABLE = {
    paging: false,
    ordering: false,
    info: false,
    dom: "<'row'<'col-sm-12 col-md-6 float-left'f>>" +
        "<'row'<'col-sm-12'tr>>",
    language: {
        emptyTable: "No Data found",
        search: "",
        searchPlaceholder: "Search...",
    }
};


/**
 * @description used for matching typeahead values
 * @param strs
 * @returns {findMatches}
 */
let substringMatcher = function (strs) {
    return function findMatches(q, cb) {
        let matches, substringRegex;

        // an array that will be populated with substring matches
        matches = [];

        // regex used to determine if a string contains the substring `q`
        substrRegex = new RegExp(q, 'i');

        // iterate through the pool of strings and for any string that
        // contains the substring `q`, add it to the `matches` array
        $.each(strs, function (i, str) {
            if (substrRegex.test(str)) {
                matches.push(str);
            }
        });

        cb(matches);
    };
};

jQuery(function () {

    /**
     * Return to Top of Page
     */
    $("#toTop,.toTop").click(function () {
        $("html, body").animate({scrollTop: 0}, 1000);
    });

});

