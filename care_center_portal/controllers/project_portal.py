from odoo import http
from odoo.http import request
from odoo.addons.project.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):

    @http.route('/my/tasks/create/', auth='user', website=True)
    def create_task(self, *args, **kw):
        qcontext = request.params.copy()
        partner = request.env.user.partner_id
        Task = request.env['project.task'].sudo().with_context({'tracking_disable': True})
        qcontext.update({
            'error': {},
            'error_message': [],
        })

        if request.httprequest.method == 'POST':
            try:
                task = Task._handle_task_post(
                    qcontext,
                    partner,
                )
                OdooBot_id = request.env['res.partner'].sudo().with_context(active_test=False).search([
                                                                                            ('name', '=', 'OdooBot'),
                                                                                        ]).mapped('id')[0]
                task.message_unsubscribe([OdooBot_id])
                task.message_subscribe([partner.id])
                return request.redirect(task.get_portal_url() + f'&status=create_success')
            except Exception as e:
                request.env.cr.rollback()
                msg = str(e)
                qcontext.update({'error_message': [msg]})
                qcontext.update(kw)

        self.prepare_task_vals(
            record=('task', Task),
            partner=partner,
            context=qcontext,
        )
        return request.render('care_center_portal.create_task', qcontext)

    def prepare_task_vals(self, record, partner, context, mode='create'):
        context.update({
            'page_name': record[0],
            'mode': mode,
            'partner': partner,
            'projects': partner.get_projects(),
        })
        context.update(dict((record,)))
