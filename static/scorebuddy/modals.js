jQuery(function () {

    /**
     * On Click of pop-modal load in the content from the href of the element.
     */
    $('#wrapper').on('click', '.pop-modal', function (e) {
        e.preventDefault();
        $('#modal-popup').modal({
            backdrop: 'static',
            keyboard: false
        }).find('.modal-content').load($(this).attr('href'));
    });

    $('#modal-popup').on('hidden.bs.modal', function (e) {
        $('#model-dynamic-content').html(
            '<div style="text-align:center">\n' +
            '    <img height="149px" width="218px" src="public/img/small-loader.gif" />\n' +
            '</div>');
    });

});

