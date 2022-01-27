jQuery(function () {

    /**
     * Initialising the Data Table
     */
    $('#data_tables').DataTable({
        processing: true,
        ajax: {
            url: "results.php",
            type: "GET",
            data: {
                "getReportData": true,
            },
        },
        deferRender: true,
        columnDefs: [
            {
                "targets": [1, 7],
                className: "no-wrap" //Add no-wrap to Employee, Team & Date Column
            }
        ],
        paging: true,
        conditionalPaging: true,
        pageLength: 100,
        lengthChange: true,
        order: [0, 'asc'], //Result ID Low to High
        pagingType: 'simple',
        orderClasses: true,
        info: true,
        dom: "<'row'<'col-sm-12 col-md-6 float-left'f><'col-sm-12 col-md-6'l>>" +
            "<'row'<'col-sm-12'tr>>" +
            "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
        language: {
            processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span>',
            loadingRecords: '',
            emptyTable: "No Scores found for the filter data selected.",
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
    });

});