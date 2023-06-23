/** @odoo-module **/

import ActivityMenu from '@mail/js/systray/systray_activity_menu';


ActivityMenu.include({
    events: _.extend({}, ActivityMenu.prototype.events, {
        'click .o_timer_action': '_onTimerFilterClick',
    }),

    _onActivityFilterClick: function (event) {
        var data = _.extend({}, this.$(event.currentTarget).data(), this.$(event.target).data());
        if (data.activity_type === 'timer') {
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'My Tasks or Followed Tasks',
                res_model: 'project.task',
                views: [[false, 'kanban'], [false, 'form'], [false, 'list'], [false, 'calendar']],
                context: {
                    'search_default_my_tasks': 1,
                    'search_default_my_followed_tasks': 1,
                },
            });
        } else {
            this._super(event);
        }
    },

    _onTimerFilterClick: function (event) {
        event.stopPropagation();
        var data = _.extend({}, $(event.currentTarget).data(), $(event.target).data());
        if (data.active_task_id) {
            this.do_action({
                type: 'ir.actions.act_window',
                name: data.active_task_name,
                res_model: 'project.task',
                res_id: data.active_task_id,
                views: [[false, 'form']],
                view_mode: 'form',
            });
        } else if (data.my_timers === 1) {
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'My Timers',
                res_model: 'project.task',
                views: [[false, 'kanban'], [false, 'form'], [false, 'list'], [false, 'calendar']],
                context: {'search_default_agent_timers': 1},
            });
        } else {
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'My Tasks',
                res_model: 'project.task',
                views: [[false, 'kanban'], [false, 'form'], [false, 'list'], [false, 'calendar']],
                context: {
                    'search_default_my_tasks': 1,
                },
            });
        }
    }

});