// requires: moment.js, lodash
/* This object provides functionality to handle filtering related data - generate urls, convert filter keys, etc */
let filteringUrlGenerator = {
    /**
     * Initializing method, setting datesHelper
     * @param datesHelper Object
     */
    init: function (datesHelper) {
        this.datesHelper = datesHelper;
    },
    // internal objects variables
    datesHelper: null,
    constants: {
        // custom dashboard filtering fields names translated to existing filed names used by report pages
        // NOTE: filter keys here need to be consistent with those defined at backend:
        // src/utility/filter/Provider/FilterFieldsProvider.php
        // TODO: *potentially* generate this JS using backend definitions, to hold only one defining place
        filterFieldKeysTranslations: {
            dateFrom: 'fromDate',
            dateTo: 'toDate',
            filterBy: 'filterDate',
            group: 'clientId',
            team: 'teamId',
            eventType: 'contactType',
            eventSubtype: 'contactSubType',
            interval: 'filterType',
            scoreCard: 'scoreSheet',
            highlightBelow: 'target',
            dataTagsArr: 'analytics-data-tags',
            logicalOperator: 'logical-operator',
            supervisor: 'teamLeader',
            evaluator: 'monitorId',
            employee: 'agent',
            category: 'formType',
            formula: 'formula',
        },
    },
    /**
     * Generates full report url applying report-tile assigned filtering
     * @param reportId String
     * @param baseUrl String
     * @param filters Object
     * @return {string}
     */
    generateReportUrl: function (reportId, baseUrl, filters) {

        let urlParams = this.generateUrlParamsFromFilters(filters);

        if (typeof urlParams.dataLimit !== 'undefined') {
            urlParams.fromDate = moment().subtract(1, 'year').format('YYYY-MM-DD');
            urlParams.toDate = moment().format('YYYY-MM-DD');
            delete urlParams.dataLimit; // removing, as this param is not supported by report pages
        }

        // translate filter keys
        urlParams = this.translateFilterKeysAndValues(reportId, urlParams);

        return baseUrl + '?' + this.convertArrayObjectToGETParams(urlParams);
    },
    /**
     * Generates data retrieval url applying report-tile assigned filtering
     * @param baseUrl String
     * @param tile Object
     * @return {string}
     * TODO: combine with FilteringHelper::buildDataUrlFromFilters() ?
     */
    generateDataUrl: function (baseUrl, tile) {

        let urlParams = this.generateUrlParamsFromFilters(tile.filters);

        // add chart data retrieval specific request params
        urlParams.reportGroup = tile.groupName;
        urlParams.reportNumber = tile.reportId;

        let chartType = tile.visualisationType.replace('chart', '');
        chartType = chartType.charAt(0).toLowerCase() + chartType.slice(1); // make first char lowercase
        urlParams.chartType = chartType;

        urlParams.chartYAxisTitle = tile.displayedValueType === 'percent' ? 'Percentage (%)' : 'Count';

        return baseUrl + '?' + this.convertArrayObjectToGETParams(urlParams);
    },
    /**
     * Creates object of filtering values based on filters
     * @param filters
     */
    generateUrlParamsFromFilters: function (filters) {

        let urlParams = {};

        // data limit
        if (typeof filters.dataLimit !== 'undefined') {
            urlParams.dataLimit = filters.dataLimit.selectedValue;
        }
        // date range
        if (typeof filters.dateRange !== 'undefined') {
            urlParams = this.datesHelper.convertDateRangeToDates(filters.dateRange.selectedValue);
        }
        // filterBy date (score|call|update)
        if (typeof filters.filterBy !== 'undefined') {
            urlParams.filterBy = filters.filterBy.selectedValue
        }
        // group
        if (typeof filters.group !== 'undefined') {
            urlParams.group = filters.group.selectedValue;
        }
        // team
        if (typeof filters.team !== 'undefined') {
            urlParams.team = filters.team.selectedValue;
        }
        // scoreCard
        if (typeof filters.scoreCard !== 'undefined') {
            urlParams.scoreCard = filters.scoreCard.selectedValue;
        }
        // event type
        if (typeof filters.eventType !== 'undefined') {
            urlParams.eventType = filters.eventType.selectedValue;
        }
        // event subtype
        if (typeof filters.eventSubtype !== 'undefined') {
            urlParams.eventSubtype = filters.eventSubtype.selectedValue;
        }
        // interval
        if (typeof filters.interval !== 'undefined') {
            urlParams.interval = filters.interval.selectedValue;
        }
        // formula
        if (typeof filters.formula !== 'undefined') {
            urlParams.formula = filters.formula.selectedValue;
        }

        return urlParams;
    },
    /**
     * Converts object representing GET parameters into GET request string
     * @param object
     * @return {string}
     */
    convertArrayObjectToGETParams: function (object) {

        return Object.keys(object).map(function (key) {

            let entityValue = object[key];

            if (typeof entityValue === 'boolean') {
                // convert boolean values into integers
                entityValue = entityValue ? 1 : 0;
            }

            let entity = key + '=' + encodeURIComponent(entityValue);

            if (
                (typeof entityValue === 'array' || typeof entityValue === 'object')
                && entityValue.length
            ) {
                let units = [];
                _.forEach(entityValue, function (singleValue) {
                    if (typeof singleValue === 'string' || typeof singleValue === 'number') {
                        units.push(key + '[]=' + encodeURIComponent(singleValue));
                    } else if (typeof singleValue === 'object') {
                        // read 'value' property if single array/object element is an object
                        units.push(key + '[]=' + encodeURIComponent(singleValue.value));
                    }
                });
                entity = units.join('&');
            }

            return entity;
        }).join('&');
    },
    /**
     * Translates filtering keys according to filter keys translation definition (this.constants.filterFieldKeysTranslations)
     * @param urlParams Object
     */
    translateFilterKeysAndValues: function (reportId, urlParams) {

        let self = this;
        let filtersTranslatedKeys = {};

        if (reportId === '3.2') {
            filtersTranslatedKeys.contactType = 'All';
        } else if (reportId === '7.1') {
            filtersTranslatedKeys.filter_submit = 1;
        }

        _.forEach(urlParams, function (filterValue, filterKey) {
            // exclusive case, different dates from-to filter keys
            // TODO: Unify filtering keys along with all other filters, then delete if statement below (2020-02-13)
            if (reportId === '4.7' && filterKey === 'scoreCard') {
                filtersTranslatedKeys['scoreSheet[]'] = filterValue;
                return;
            }
            if (reportId === '7.1') {
                if (filterKey === 'dateFrom') {
                    filtersTranslatedKeys['from'] = filterValue;
                }
                if (filterKey === 'dateTo') {
                    filtersTranslatedKeys['to'] = filterValue;
                }
            }

            if (typeof self.constants.filterFieldKeysTranslations[filterKey] !== 'undefined') {
                // translate key, if exists in translation array
                filtersTranslatedKeys[self.constants.filterFieldKeysTranslations[filterKey]] = filterValue;
            } else {
                // use original key otherwise
                filtersTranslatedKeys[filterKey] = filterValue;
            }

        });

        return filtersTranslatedKeys;
    },
};

window.FilteringUrlGenerator = filteringUrlGenerator;
