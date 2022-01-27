// requires: jQuery
/**
 * @author Adam Okon <aokon@sentient.ie>
 * Vue wrapper for jQuery Chosen plugin
 */
window.VueChosenComponent = {
    delimiters: ['[[', ']]'],
    props: {
        value: [String, Array],
        multiple: Boolean,
        required: Boolean,
        options: Array
    },
    template: `<select class="chosen-select" :multiple="multiple" :required="required">
    <slot></slot>
    <option v-for="option in options"
            :selected="isSelected(option.value)"
            :value="option.value">[[ option.text ]]
    </option>
    </select>`,
    mounted: function () {
        let self = this;

        jQuery(this.$el)
            .val(this.value)
            .chosen({
                width: "100%",
                placeholder_text_multiple: "Select value",
            })
            .on("change", function (event) {
                self.$emit('input', jQuery(self.$el).val())
            });
    },
    updated: function () {
        jQuery(this.$el).trigger('chosen:updated');
        this.$emit('change');
    },
    watch: {
        value: function (val) {
            jQuery(this.$el).val(val).trigger('chosen:updated');
        }
    },
    methods: {
        isSelected: function (value) {
            if (this.multiple) {
                return _.indexOf(this.value, value) !== -1;
            }

            return this.value === value;
        }
    }
};
