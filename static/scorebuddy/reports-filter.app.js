Vue.use(EndpointUrls);
Vue.use(DatesHelper);
Vue.use(FilteringUrlGenerator);
Vue.use(vuejsDatepicker);
Vue.use(VueChosenComponent);
Vue.use(Cookies);
let reportsFilterApp = new Vue({
    delimiters: ['[[', ']]'],
    components: {
        datepicker: vuejsDatepicker,
        chosenSelect: VueChosenComponent,
    },
    productionTip: false,
    el: '#analyticsFilter',
    data: {
        config: {
            dateFormatISO: 'YYYY-MM-DD',
            dateFormat: '',
            dateFormatJS: '',
            mondayFirst: false,
            disabledDates: {
                from: new Date(),
            },
            // ordering of the fields below matters, used for dropdowns update, see details in the code
            filterFieldsSupportedOrder: [
                'initial',
                'dateRange',
                'interval',
                'dateFrom',
                'dateTo',
                'filterBy',
                'group',
                'team',
                'scoreCard',
                'scoreCardCurrentTeamRestrictions',
                'surveyId',
                'questionIds',
                'dataTagsArr',
                'logicalOperator',
                'eventType',
                'eventSubtype',
                'supervisor',
                'employee',
                'employeeCurrentTeamRestrictions',
                'evaluator',
                'category',
                'highlightBelow',
                'countOrPercentage',
                'formula',
                'section',
                'sectionCurrentTeamRestrictions',
                'question',
                'questionNumber',
                'formVersion',
                'banNumber',
            ],
            filterPersistedParamsCookieName: 'filterPersistedParams',
        },
        // currently selected filter parameters, keyed by filter field name
        selectedParams: {
            dataTagsArr: [],
        },
        fieldsDefinition: {
            fields: [],
            defaults: [],
            locks: [],
            optionAll: [],
            optionSelectValue: [],
            optionNoData: [],
        },
        fieldsOptions: {},
        // parameters that are not used to generate filtered url, but are displayed within the filter
        intermediaryParams: {
            // filter date parameters are kept in ISO format for easier API calls, this ones are for display only
            dateFrom: null,
            dateTo: null,
            weekFrom: null,
            weekTo: null,
            dateRange: null,
        },
        watchers: {
            // below are informative initialized holders for unwatch functions, created by watchers functions
            dateFromIntermediary: null,
            dateToIntermediary: null,
            weekFromIntermediary: null,
            weekToIntermediary: null,
        },
        requestPending: false,
        persistedParams: {
            toggleAdvanced: false,
        },
    },
    created: function () {
        // initialize FilteringUrlGenerator
        FilteringUrlGenerator.init(DatesHelper);
        this.loadPersistedParams();
    },
    computed: {
        /**
         * Week number used in weeks dropdowns; always up to the number of weeks existing in current year
         * @return Integer
         */
        weekNumber: function () {
            return moment().week();
        },
        /**
         * Returns request params less the fields containing the value '-1-', which is for field option 'Select value'
         */
        sanitizedSelectedParams: function () {
            return _.pickBy(this.selectedParams, function (paramValue) {
                // return paramValue !== -1;
                return (typeof paramValue !== 'undefined')
                    && paramValue != -1
                    && paramValue !== false
                    && paramValue !== null;
            });
        }
    },
    watch: {
        persistedParams: {
            handler: function () {
                this.persistPersistedParams();
            },
            deep: true
        }
    },
    methods: {
        /**
         * Performs a coall to API to get filtering options for all fields existing in the filter
         * @return {Promise<void>}
         */
        getInitialFilterOptions: async function () {

            await this.handleFieldValueChanged('initial', 'initial');

            // adding dynamic watchers
            this.watchDateIntermediary('From');
            this.watchDateIntermediary('To');
            this.watchWeeksIntermediary('From');
            this.watchWeeksIntermediary('To');
            this.watchDateRange();
        },
        /**
         * Sets fields available options
         * @param fieldsOptions
         */
        setFieldsOptions: function (fieldsOptions) {

            let self = this;

            _.forIn(fieldsOptions, function (fieldValues, fieldName) {
                self.setSingleFieldOptions(fieldName, fieldValues);
            });
        },
        /**
         * Sets single filter field options; prepends with 'select value' item if needed
         * @param string fieldName
         * @param array|object fieldOptions
         */
        setSingleFieldOptions: function (fieldName, fieldOptions) {

            this.fieldsOptions[fieldName] = _.values(fieldOptions);

            if (this.hasSelectAllOption(fieldName)) {
                this.fieldsOptions[fieldName].unshift({value: 'All', text: 'All'});
            }
            if (this.hasSelectValueOption(fieldName) && !this.isMultiple(fieldName)) {
                this.fieldsOptions[fieldName].unshift({value: '', text: '--- Select value ---'});
            }

            this.$forceUpdate();
        },
        /**
         * Set date upon week number selection
         * @param FromOrTo String
         * @param weekNumber Int|String
         */
        setDateByWeekNumber: function (FromOrTo, weekNumber) {
            let newDateMoment;
            if (weekNumber === 1) {
                newDateMoment = moment(moment().format('YYYY') + '-01-01');
            } else {
                newDateMoment = moment(moment().format('YYYY') + '-01-01').add(parseInt(weekNumber, 10) - 1, 'weeks').startOf('isoWeek');
            }


            this.watchers['date' + FromOrTo + 'Intermediary'](); // removing watcher to not go into infinite loop
            // set date for date-picker
            this.intermediaryParams['date' + FromOrTo] = newDateMoment.toDate();
            this.watchDateIntermediary(FromOrTo); // adding watcher back in

            // set internal iso date for requests
            this.selectedParams['date' + FromOrTo] = newDateMoment.format(this.config.dateFormatISO);
        },
        /**
         * Gets default value for filter field, either from defaults, or just first value from options list
         * @param field
         * @return {*}
         */
        getDefaultValueForField: function (field) {
            // set default value, if defined
            if (typeof this.fieldsDefinition.defaults[field] !== 'undefined') {
                return this.fieldsDefinition.defaults[field];
            }
            // set first value from available list, if only its not an object (multi-select fields)
            if (this.fieldsOptions[field] && this.fieldsOptions[field][0] && typeof this.fieldsOptions[field][0] !== 'object') {
                return this.fieldsOptions[field][0];
            }

            return this.isMultiple(field) ? [] : null;
        },

        /** WATCHERS */

        /**
         * Watcher for dateRange changes
         */
        watchDateRange: function () {

            let self = this;

            this.watchers['dateRange'] = this.$watch(
                'intermediaryParams.dateRange',
                function (newValue) {
                    let dates = DatesHelper.convertDateRangeToDates(newValue, self.config.dateFormatISO);
                    // set internal ISO dates
                    self.selectedParams.dateFrom = dates.dateFrom;
                    self.selectedParams.dateTo = dates.dateTo;

                    let dateFromMoment = moment(dates.dateFrom);
                    let dateToMoment = moment(dates.dateTo);

                    // set datepicker dates
                    self.intermediaryParams.dateFrom = dateFromMoment.toDate();
                    self.intermediaryParams.dateTo = dateToMoment.toDate();

                    // set week selector dates
                    self.intermediaryParams.weekFrom = self.getWeekNumberFromMomentDate(dateFromMoment);
                    self.intermediaryParams.weekTo = self.getWeekNumberFromMomentDate(dateToMoment);
                }
            );
        },
        /**
         * Dynamic date-from/to intermediary (the one ofr date picker) watch function creator
         * @param fromOrTo
         */
        watchDateIntermediary: function (fromOrTo) {

            let self = this;

            this.watchers['date' + fromOrTo + 'Intermediary'] = this.$watch(
                'intermediaryParams.date' + fromOrTo,
                function (newValue) {

                    if (fromOrTo === 'From' && self.intermediaryParams.dateTo < newValue) {
                        self.intermediaryParams.dateTo = newValue;
                    }
                    if (fromOrTo === 'To' && self.intermediaryParams.dateFrom > newValue) {
                        self.intermediaryParams.dateFrom = newValue;
                    }

                    // check if date range is not exceeding 5 years
                    let daysDiff = Math.floor(
                        (self.intermediaryParams.dateTo - self.intermediaryParams.dateFrom) / (1000 * 60 * 60 * 24)
                    );

                    if (daysDiff > (365 * 5)) {
                        return;
                    }

                    self.selectedParams.dateTo = moment(self.intermediaryParams.dateTo).format(self.config.dateFormatISO);
                    self.selectedParams.dateFrom = moment(self.intermediaryParams.dateFrom).format(self.config.dateFormatISO);
                    // update week value, disabling its watcher for time of update
                    self.watchers['week' + fromOrTo + 'Intermediary'](); // removing week watcher to not trigger cascade date update
                    self.intermediaryParams['week' + fromOrTo] = self.getWeekNumberFromMomentDate(moment(newValue));
                    self.watchWeeksIntermediary(fromOrTo); // add watcher back in
                }
            );
        },
        /**
         * Dynamic week-from/to intermediary watch function creator
         * @param fromOrTo
         */
        watchWeeksIntermediary: function (fromOrTo) {

            let self = this;

            this.watchers['week' + fromOrTo + 'Intermediary'] = this.$watch(
                'intermediaryParams.week' + fromOrTo,
                function (newValue) {
                    self.setDateByWeekNumber(fromOrTo, newValue);
                    if (
                        fromOrTo === 'From'
                        && (self.intermediaryParams.weekTo < newValue || self.intermediaryParams.weekTo > self.weekNumber)
                    ) {
                        self.intermediaryParams.weekTo = newValue;

                    }
                }
            );
        },
        /**
         * Dynamic multi filter-field watch function creator
         * @param fieldName
         */
        watchFilterField: function (fieldName) {

            let self = this;

            this.watchers[fieldName] = this.$watch(
                'selectedParams.' + fieldName,
                async function (newValue) {
                    if (fieldName === 'dateFrom' && this.selectedParams.dateTo < this.selectedParams.dateFrom) {
                        this.intermediaryParams.dateFrom = moment(this.selectedParams.dateTo).toDate();
                    }
                    // hold requests with invalid date range; this app will wix them, then update all could go out
                    if (this.selectedParams.dateTo < this.selectedParams.dateFrom) {
                        return true;
                    }
                    await self.handleFieldValueChanged(fieldName);
                }
            );
        },
        /**
         * Retrieves filtering options from API, apply them to relevant filter dropdowns; update currently selected values to defaults
         * @return {Promise<boolean>}
         */
        handleFieldValueChanged: async function (fieldName, routeName) {
            let self = this;

            let routeNameEffective = (typeof routeName === 'undefined') ?
                (fieldName + 'Changed&') :
                (routeName + '&');

            let requestUrl = EndpointUrls.FILTERING_CHANGES_GET
                + '?route=' + routeNameEffective
                + FilteringUrlGenerator.convertArrayObjectToGETParams(this.sanitizedSelectedParams)
                + '&requestedFields[]=' + self.fieldsDefinition.fields.join('&requestedFields[]=') // expected ersponse fields
                + '&includeStaticFields=1';

            // set request to pending state, to let frontend 'processing' indicator be shown
            this.requestPending = true;

            await $.ajax({
                url: requestUrl,
                type: 'GET',
                dataType: 'json'
            }).always(function () {
                self.requestPending = false;
            }).done(function (response) {
                //  get list of fields 'below' the one that changed, and change options for those only
                let applicableFields = [];
                _.forEach(self.config.filterFieldsSupportedOrder, function (supportedFieldName, index) {
                    if (index > _.indexOf(self.config.filterFieldsSupportedOrder, fieldName)) {
                        applicableFields.push(supportedFieldName);
                    }
                });

                // update field options
                _.forIn(applicableFields, function (fieldName) {

                    if (typeof response[fieldName] !== 'undefined' && response[fieldName] !== null) {
                        self.setSingleFieldOptions(fieldName, response[fieldName]);
                    }
                    if (routeName !== 'initial' && fieldName !== 'dateFrom' && fieldName !== 'dateTo' && !self.isLocked(fieldName)) {
                        // put default values in dependent fields, as available options list might change
                        self.selectedParams[fieldName] = self.getDefaultValueForField(fieldName);
                    }
                });
            }).fail(function (xhr) {
                let data = JSON.parse(xhr.responseText);
                alertify.error(data.error);
            }).catch(function (e) {
            });
        },
        /**
         * Sets relevant date-range value, calculating from dates
         * @param dateFrom String ISO date
         * @param dateTo String ISO date
         */
        getRelevantDateRangeValue: function (dateFrom, dateTo) {

            let self = this;
            let matchingInterval = 'custom';

            _.forEach(DatesHelper.availableReportPageIntervals, function (intervalName) {
                let dates = DatesHelper.convertDateRangeToDates(intervalName, self.config.dateFormatISO);
                if (dates.dateFrom === dateFrom && dates.dateTo === dateTo) {
                    matchingInterval = intervalName;
                    return false;
                }
            });

            return matchingInterval;
        },
        /**
         * Submits filter by reloading page with new GET params
         * @return {Promise<void>}
         */
        submitFilter: async function () {
            if (checkRequired()) {
                alertify.warning('Please fill in the required fields.');
                return false;
            }

            let filterParams = FilteringUrlGenerator.translateFilterKeysAndValues('custom', this.sanitizedSelectedParams);
            let urlParamsString = '?' + FilteringUrlGenerator.convertArrayObjectToGETParams(filterParams);

            window.location.replace(urlParamsString);
        },
        /**
         * TODO: Make it working by adding backend support
         */
        filterReset: function () {
            window.location.replace('?filterReset=1');
        },
        /** INITIAL SETTERS, called on app object upon its initialization */

        /**
         * Sets filtering parameters in app
         * @param filterParamValues
         */
        setFilterParamValues: function (filterParamValues) {

            let self = this;

            // initialize picker dates to today
            this.intermediaryParams.dateFrom = moment().toDate();
            this.intermediaryParams.dateTo = moment().toDate();

            // fill in selectedValues field values
            _.forIn(this.fieldsDefinition.fields, function (fieldName) {

                if (fieldName === 'dateRange') {
                    // we don't need this field in selectedValues, as it is not used to build request url(s)
                    return;
                }

                if (typeof filterParamValues[fieldName] !== 'undefined'
                    && filterParamValues[fieldName] !== false
                    && filterParamValues[fieldName] !== null
                    && filterParamValues[fieldName] !== ''
                ) {
                    self.$set(self.selectedParams, fieldName, filterParamValues[fieldName]);
                } else {
                    self.$set(self.selectedParams, fieldName, self.getDefaultValueForField(fieldName));
                }
            });

            // initialize also datepicker dates, if they were provided
            if (typeof filterParamValues.dateFrom !== 'undefined' && filterParamValues.dateFrom.length === 10) {
                let dateFromMoment = moment(filterParamValues.dateFrom);
                this.intermediaryParams.dateFrom = dateFromMoment.toDate();
                this.intermediaryParams['weekFrom'] = this.getWeekNumberFromMomentDate(dateFromMoment);
            }
            if (typeof filterParamValues.dateTo !== 'undefined' && filterParamValues.dateTo.length === 10) {
                let dateToMoment = moment(filterParamValues.dateTo);
                this.intermediaryParams.dateTo = dateToMoment.toDate();
                this.intermediaryParams['weekTo'] = this.getWeekNumberFromMomentDate(dateToMoment);
            }

            // set relevant date-range value
            this.intermediaryParams.dateRange = this.getRelevantDateRangeValue(
                this.selectedParams.dateFrom,
                this.selectedParams.dateTo
            );

            // set watchers for dates from/to; other fields will trigger update as per 'onchange' event for each of them, to not trigger cascade updates calls
            this.watchFilterField('dateFrom');
            this.watchFilterField('dateTo');
        },
        /**
         * Gets week number - only for current year!
         * @param dateMoment
         */
        getWeekNumberFromMomentDate: function (dateMoment) {

            let week = (dateMoment.year() === new Date().getFullYear()) ?
                dateMoment.week() :
                null;

            return week;
        },
        /**
         * Sets fields definition; parses dates if passed in relative format
         * @param fieldsDefinition
         */
        setFilterDefinition: function (fieldsDefinition) {

            this.fieldsDefinition = fieldsDefinition;
        },
        /**
         * Sets (moment.js format) date format; also sets standard JS date format
         * @param dateFormat
         */
        setDateFormat: function (dateFormat) {
            // set date format for Moment.js
            this.config.dateFormat = dateFormat;
            // set JS format for datepicker
            this.config.dateFormatJS = (
                (
                    dateFormat.split('D').join('d')
                ).split('Y').join('y')
            ).split('-').join('/');
            // initialize DateHelpers internal date format
            DatesHelper.init(dateFormat);
        },
        /**
         * Checks of given field has 'select value' option to be existent
         * @param fieldName
         * @return {boolean}
         */
        hasSelectValueOption: function (fieldName) {

            return _.indexOf(this.fieldsDefinition.optionSelectValue, fieldName) !== -1;
        },
        isMultiple: function (fieldName) {

            return _.indexOf(this.fieldsDefinition.multiple, fieldName) !== -1;
        },
        /**
         * Checks of given field has 'select value' option to be existent
         * @param fieldName
         * @return {boolean}
         */
        hasSelectAllOption: function (fieldName) {

            return _.indexOf(this.fieldsDefinition.optionAll, fieldName) !== -1;
        },
        /**
         * Checks of given field has 'no data' option to be existent
         * @param fieldName
         * @return {boolean}
         */
        hasNoDataOption: function (fieldName) {

            return _.indexOf(this.fieldsDefinition.optionNoData, fieldName) !== -1;
        },
        /**
         * Checks of given field has 'select value' option to be existent
         * @param fieldName
         * @return {boolean}
         */
        isLocked: function (fieldName) {

            return _.indexOf(this.fieldsDefinition.locks, fieldName) !== -1;
        },
        /**
         * Chgecks if field is type of multiple select
         * @param fieldName
         * @return {boolean}
         */
        isMultiple: function (fieldName) {

            return _.indexOf(this.fieldsDefinition.multiple, fieldName) !== -1;
        },
        /**
         * Loads persisted filter params (currently: from cookie)
         */
        loadPersistedParams: function () {
            let persistedData = Cookies.getJSON(this.config.filterPersistedParamsCookieName);
            if (typeof persistedData !== 'undefined') {
                this.persistedParams = persistedData;
            }
        },
        /**
         * Gets filter persisted param
         */
        getPersistedParam: function (paramName) {
            return (typeof this.persistedParams[paramName] !== 'undefined') ?
                this.persistedParams[paramName] :
                null;
        },
        /**
         * Persists filter params (currently: in cookie)
         */
        persistPersistedParams: function () {
            Cookies.set(
                this.config.filterPersistedParamsCookieName,
                JSON.stringify(this.persistedParams),
                {path: ''}
            );
        }
    },

});

window.ReportsFilterApp = reportsFilterApp;
