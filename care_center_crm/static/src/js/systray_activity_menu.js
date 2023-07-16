/** @odoo-module **/
import ActivityMenu from '@mail/js/systray/systray_activity_menu';


ActivityMenu.include({
    /**
     * Redirect to particular model view
     * @private
     * @param {MouseEvent} event
     */
    _onActivityFilterClick: function (event) {

        let data = _.extend({}, $(event.currentTarget).data(), $(event.target).data());
        let call_filter = data.filter;
        let action_name = data.model_name;
        if (data.res_model === 'crm.phonecall') {
            let context = {'search_default_my_phonecalls': 1, 'search_default_my_team': 1};
            if (call_filter === 'my') {
                action_name = 'My ' + action_name;
                context['search_default_phonecalls_overdue'] = 1;
                context['search_default_phonecalls_today'] = 1;
                context['search_default_phonecalls_planned'] = 1;
            } else if (call_filter === 'upcoming_all') {
                context['search_default_phonecalls_planned'] = 1;
            } else {
                context['search_default_phonecalls_' + data.filter] = 1;
            }
            if (call_filter === 'overdue') {
                action_name = 'Overdue ' + action_name;
            }

            this.do_action({
                type: 'ir.actions.act_window',
                name: action_name,
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
