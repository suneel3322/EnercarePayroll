jQuery(function () {

    /**
     * Toggling between Percentage and Numeric View.
     */
    $("#percentageToggleBtn").on("click", function () {

        let percentageRow = $(".percentageRow");

        percentageRow.toggle();
        $(".numericRow").toggle();
        $('#percentageToggleBtn i').toggleClass("fa-toggle-off fa-toggle-on");

        /**
         * Additional Functionality to update the view in the URL params
         * @type {*|define.amd.jQuery|HTMLElement}
         */
        let downloadLink = $("#downloadXLS");
        if (downloadLink.length) {
            let view = 'count';
            if (percentageRow.is(":visible")) {
                view = 'percent';
            }

            let params = new URLSearchParams(downloadLink.attr('href'));
            params.set('countOrPercentage', view);
            params.toString();

            downloadLink.attr('href', params.toString().replace("%3F", "?"));
        }

    });

});