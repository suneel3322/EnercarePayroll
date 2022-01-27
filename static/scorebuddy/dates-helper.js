let datesHelper = {
    dateFormat: 'YYYY-MM-DD',
    init: function (dateFormat) {
        this.dateFormat = dateFormat;
    },
    /**
     * Converts date-range strong int from/to dates
     * @param dateRange String
     * @return {{dateTo: *, dateFrom: string}}
     */
    convertDateRangeToDates: function (dateRange, dateFormat) {

        let dateFormatApplicable = this.dateFormat;

        if (typeof dateFormat !== 'undefined') {
            dateFormatApplicable = dateFormat;
        }

        let dates = {
            dateFrom: '',
            dateTo: moment().format(dateFormatApplicable), // today
        };
        // list of dateRange identifiers needs to be consistent with one defined in:
        // src/CustomDashboards/Provider/Filter/CustomDashboardsFieldValuesProvider.php
        switch (dateRange) {
            case 'lastWeek':
                dates.dateFrom = moment().subtract(1, 'week').startOf('week').format(dateFormatApplicable);
                dates.dateTo = moment().subtract(1, 'week').endOf('week').format(dateFormatApplicable);
                break;
            case 'last4Weeks':
                dates.dateFrom = moment().subtract(4, 'week').format(dateFormatApplicable);
                break;
            case 'lastMonth':
                dates.dateFrom = moment().subtract(1, 'month').startOf('month').format(dateFormatApplicable);
                dates.dateTo = moment().subtract(1, 'month').endOf('month').format(dateFormatApplicable);
                break;
            case 'last2Months':
                dates.dateFrom = moment().subtract(2, 'month').format(dateFormatApplicable);
                break;
            case 'last3Months':
                dates.dateFrom = moment().subtract(3, 'month').format(dateFormatApplicable);
                break;
            case 'lastQuarter':
                dates.dateFrom = moment().subtract(1, 'quarter').startOf('quarter').format(dateFormatApplicable);
                dates.dateTo = moment().subtract(1, 'quarter').endOf('quarter').format(dateFormatApplicable);
                break;
            case 'last4Months':
                dates.dateFrom = moment().subtract(4, 'month').format(dateFormatApplicable);
                break;
            case 'last5Months':
                dates.dateFrom = moment().subtract(5, 'month').format(dateFormatApplicable);
                break;
            case 'last6Months':
                dates.dateFrom = moment().subtract(6, 'month').format(dateFormatApplicable);
                break;
            case 'lastYear':
                dates.dateFrom = moment().subtract(1, 'year').startOf('year').format(dateFormatApplicable);
                dates.dateTo = moment().subtract(1, 'year').endOf('year').format(dateFormatApplicable);
                break;
            /* ranges for report pages filter */
            case 'today':
                dates.dateFrom = dates.dateTo;
                break;
            case 'yesterday':
                dates.dateFrom = dates.dateTo = moment().subtract(1, 'day').format(dateFormatApplicable);
                break;
            case 'thisWeek':
                dates.dateFrom = moment().startOf('week').format(dateFormatApplicable);
                break;
            case 'thisMonth':
                dates.dateFrom = moment().startOf('month').format(dateFormatApplicable);
                break;
            case 'thisQuarter':
                dates.dateFrom = moment().startOf('quarter').format(dateFormatApplicable);
                break;
            case 'thisYear':
                dates.dateFrom = moment().startOf('year').format(dateFormatApplicable);
                break;
            case 'custom':
                dates.dateFrom = dates.dateTo;
                break;
            default:
                dates.dateFrom = moment().subtract(1, 'week').format(dateFormatApplicable);
                break;
        }

        return dates;
    },
    /**
     * Intervals available for report pages (NOT Custom Dahsboards filter)
     */
    availableReportPageIntervals: ['today', 'yesterday', 'thisWeek', 'lastWeek', 'thisMonth', 'lastMonth', 'thisQuarter', 'lastQuarter', 'thisYear', 'lastYear']
};

window.DatesHelper = datesHelper;
