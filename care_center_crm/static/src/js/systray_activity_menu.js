odoo.define('care_center_crm.systray.ActivityMenu', function (require) {
"use strict";

var ActivityMenu = require('mail.systray.ActivityMenu');

ActivityMenu.include({
    /**
     * Redirect to particular model view
     * @private
     * @param {MouseEvent} event
     */
    _onActivityFilterClick: function (event) {

        var data = _.extend({}, $(event.currentTarget).data(), $(event.target).data());
        var call_filter = data.filter;
        if (data.res_model === 'crm.phonecall') {
            var context = {};
            if (call_filter === 'my') {
                context['search_default_phonecalls_overdue'] = 1;
                context['search_default_phonecalls_today'] = 1;
                context['search_default_phonecalls_planned'] = 1;
            } else if (call_filter === 'upcoming_all') {
                context['search_default_phonecalls_planned'] = 1;
            } else {
                context['search_default_phonecalls_' + data.filter] = 1;
            }
            this.do_action({
                type: 'ir.actions.act_window',
                name: data.model_name,
                res_model:  data.res_model,
                views: [[false, 'list'], [false, 'form']],
                search_view_id: [false],
                context:context,
            });
        } else {
            this._super(event);
        }

    },

});
});
