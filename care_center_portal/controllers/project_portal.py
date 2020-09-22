from odoo import http, tools
from odoo.http import request
from odoo.addons.project.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):

    @http.route('/my/tasks/create/', auth='user', website=True)
    def create_task(self, **kw):
        qcontext = request.params.copy()
        partner = request.env.user.partner_id
        Task = request.env['project.task'].sudo().with_context({'tracking_disable': True})
        qcontext.update({
            'error': {},
            'error_message': [],
        })

        if request.httprequest.method == 'POST':
            form_error = self.task_form_validate(kw, qcontext)
            if not form_error:
                try:
                    task = Task._handle_task_post(
                        qcontext,
                        partner,
                    )
                    admin = request.env['res.partner'].sudo().with_context(
                        active_test=False
                    ).search([
                        ('name', '=', 'Compass ERP'),
                    ]).mapped('id')[0]
                    task.message_unsubscribe([admin])
                    task.message_subscribe([partner.id] +
                                           task.team_id.member_ids.mapped('partner_id').ids)
                    return request.redirect(task.get_portal_url() + f'&status=create_success')
                except Exception as e:
                    self._handle_exception(e, qcontext, kw)

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

    def _check_mandatory(self, data, fields, error, error_message):
        """
        Make sure mandatory fields have values and handle errors if not
        :param data: dict, data common from form POST
        :param fields: collection, fields to make sure have a value
        :param error: dict, holding which fields are in an error state
        :param error_message: list->str, holding error messages
        """
        for field_name in fields:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append('Some required fields are empty.')

    @staticmethod
    def _check_email(data, error, error_message):
        """
        Make sure email field is a valid address
        :param data: dict, data common from form POST
        :param error: dict, holding which fields are in an error state
        :param error_message: list->str, holding error messages
        """
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append('Invalid Email! Please enter a valid email address.')

    @staticmethod
    def _check_numeric(data, fields, error, error_message, check_punc=False):
        """
        Made sure all numeric fields are numbers and handle errors if not
        :param data: dict, data common from form POST
        :param fields: collection, fields to make sure have a value
        :param error: dict, holding which fields are in an error state
        :param error_message: list->str, holding error messages
        """
        for field_name in fields:
            field = data.get(field_name)
            letters = any(c.isalpha() for c in field)
            all_digits = all(c.isdigit() for c in field)
            failed = False
            if check_punc:
                if not all_digits:
                    failed = True
                    error_message.append('Numeric field may only contain letters')
            elif letters:
                failed = True
                error_message.append('Numeric field may not contain letters')
            if failed:
                error[field_name] = 'invalid'

    def _form_validate(
        self,
        data,
        fields,
        check_mandatory=True,
        check_email=True,
        check_numeric=True,
        check_punc=False
    ):
        """
        Check all form data is correct
        :param data: dict, data common from form POST
        :param fields: dict, keys(str) of types of fields values(collection) of field names
        :param check_mandatory: bool, whether to check mandatory fields
        :param check_email: bool, whether to check for a valid email
        :param check_numeric: bool, whether to check if numeric fields are correct
        :return: dict:list, fields that contain errors:error messages
        """
        error = dict()
        error_message = []

        if check_mandatory:
            self._check_mandatory(data, fields['mandatory'], error, error_message)
        if check_email:
            self._check_email(data, error, error_message)
        if check_numeric:
            self._check_numeric(data, fields['numeric'], error, error_message, check_punc)

        return error, error_message

    def task_form_validate(self, data, context):
        form_error, error_message = self._form_validate(
            data,
            {
                'mandatory': ['name', 'project_id', 'description'],
            },
            check_numeric=False,
        )
        context.update({'error': form_error, 'error_message': error_message})
        context.update(data)
        return form_error

    def _handle_exception(self, msg, context, values):
        request.env.cr.rollback()
        msg = str(msg)
        if context['name'] in msg:
            msg = f"Device name {context['name']} already exists!"
        if 'username' in msg:
            partner = request.env['res.partner'].sudo().browse(int(context['contact_id']))
            msg = msg.replace("None", partner.username).replace('(',
                                                                '').replace(')',
                                                                            '').replace("'", '', 2)
        context.update({'error_message': [msg]})
        context.update(values)
