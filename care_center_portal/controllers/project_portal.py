from odoo import http
from odoo.http import request
from odoo.addons.project.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):

    @http.route('/my/tasks/create/', auth='user', website=True)
    def portal_create_task(self, *args, **kw):
        qcontext = request.params.copy()
        user = request.env.user

        projects = user.get_projects()

        if request.httprequest.method == 'POST':
            return self.handle_post(
                qcontext,
                projects,
                user.partner_id,
            )

        return request.render(
            'care_center_portal.portal_create_task_form',
            {'projects': projects, 'page_name': 'ticket_create', 'mode': 'create'},
        )

    def handle_post(self, context, projects, partner, mode='create'):
        values = {
            key: context.get(key)
            for key in ('project_id', 'name', 'partner_id', 'description')
        }
        values['project_id'] = int(values['project_id'])
        if projects:
            team = projects.browse(values['project_id']).mapped('team_id')
            values['team_id'] = team.id
        else:
            values.pop(values['project_id'], None)

        values['user_id'] = False

        Task = request.env['project.task'].sudo()
        task = Task.create(values)
        task = task.with_context({'tracking_disable': True})
        #  Remove system from followers & add portal user
        task.message_unsubscribe((15783,))
        task.message_subscribe((partner.id,))
        if task:
            return request.redirect(task.get_portal_url() + f'&status={mode}_success')
        return request.redirect(task.get_portal_url() + f'&status={mode}_failed')
