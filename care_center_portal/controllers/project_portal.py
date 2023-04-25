from collections import OrderedDict
from operator import itemgetter

from odoo import http, tools, _
from odoo.http import request
from odoo.tools import groupby as groupbyelem
from odoo.osv.expression import OR

from odoo.addons.project.controllers.portal import CustomerPortal as CP
from odoo.addons.portal.controllers.portal import pager as portal_pager


class CustomerPortal(CP):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values['project_count'] = request.env['project.project'].search_count([
            ('message_partner_ids', 'child_of', partner.commercial_partner_id.id)
        ])
        values['task_count'] = request.env['project.task'].search_count([
            ('project_id.message_partner_ids', 'child_of', partner.commercial_partner_id.id)
        ])
        return values

    @http.route(
        [
            '/my/projects',
            '/my/projects/page/<int:page>',
            '/my/companies/<int:partner_id>/projects',
            '/my/contacts/<int:partner_id>/projects',
            '/my/companies/<int:partner_id>/projects/page/<int:page>',
            '/my/contacts/<int:partner_id>/projects/page/<int:page>',
        ],
        type='http',
        auth="user",
        website=True,
    )
    def list_projects(
        self, page=1, date_begin=None, date_end=None, sortby=None, partner_id=None, **kw
    ):
        """
        Override 'portal_my_projects' (not calling super) in addons/project/controllers/portal.py.  Needed to be done
        for supporting other companies projects for tasks (tasks are related/based off projects) not related to logged
        in user. Added partner routes & partner_id param.
        """
        values = self._prepare_portal_layout_values()
        Project = request.env['project.project']

        partner = request.env['res.partner'].sudo().browse(partner_id)
        if not partner:
            partner = request.env.user.partner_id

        # Made domain based off passed in partner_id
        domain = [('message_partner_ids', 'child_of', partner.commercial_partner_id.id)]

        searchbar_sortings = {
            'date': {
                'label': _('Newest'),
                'order': 'create_date desc'
            },
            'name': {
                'label': _('Name'),
                'order': 'name'
            },
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('project.project', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # projects count
        project_count = Project.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/projects",
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby
            },
            total=project_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        projects = Project.search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset']
        )
        request.session['my_projects_history'] = projects.ids[:100]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'projects': projects,
            'page_name': 'project',
            'archive_groups': archive_groups,
            'default_url': '/my/projects',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'partner':
            partner,  # pass partner so when going from other companies records it shows the right company.
        })
        return request.render("project.portal_my_projects", values)

    @http.route(
        [
            '/my/project/<int:project_id>',
            '/my/companies/<int:partner_id>/project/<int:project_id>',
            '/my/contacts/<int:partner_id>/project/<int:project_id>',
        ],
        type='http',
        auth="public",
        website=True,
    )
    def detail_project(self, project_id=None, access_token=None, partner_id=None, **kw):
        """
        Override 'portal_my_project' from addons/project/controllers/portal.py to add partner to qcontext
        """
        response = super().portal_my_project(int(project_id), access_token, **kw)

        partner = request.env['res.partner'].sudo().browse(partner_id)
        if not partner:
            partner = request.env.user.partner_id
        response.qcontext['partner'] = partner

        return response

    @http.route(
        [
            '/my/tasks',
            '/my/tasks/page/<int:page>',
            '/my/companies/<int:partner_id>/tasks',
            '/my/contacts/<int:partner_id>/tasks',
            '/my/companies/<int:partner_id>/tasks/page/<int:page>',
            '/my/contacts/<int:partner_id>/tasks/page/<int:page>',
        ],
        type='http',
        auth="user",
        website=True,
    )
    def list_tasks(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in='content',
        groupby='project',
        partner_id=None,
        **kw
    ):
        """
        Override 'portal_my_tasks' (not calling super) in addons/project/controllers/portal.py.  Needed to be done for
        supporting tasks for records (eg. devices) not related to logged in user.  Added partner routes & partner_id param.
        """
        values = self._prepare_portal_layout_values()

        partner = request.env['res.partner'].sudo().browse(partner_id)
        if not partner:
            partner = request.env.user.partner_id

        searchbar_sortings = {
            'date': {
                'label': _('Newest'),
                'order': 'create_date desc'
            },
            'name': {
                'label': _('Title'),
                'order': 'name'
            },
            'stage': {
                'label': _('Stage'),
                'order': 'stage_id'
            },
            'update': {
                'label': _('Last Stage Update'),
                'order': 'date_last_stage_update desc'
            },
        }
        searchbar_filters = {
            'all': {
                'label':
                _('All'),
                # Revamped domain to be based off passed in partner_id
                'domain':
                [('project_id.message_partner_ids', 'child_of', partner.commercial_partner_id.id)]
            },
        }
        searchbar_inputs = {
            'content': {
                'input': 'content',
                'label': _('Search <span class="nolabel"> (in Content)</span>')
            },
            'message': {
                'input': 'message',
                'label': _('Search in Messages')
            },
            'customer': {
                'input': 'customer',
                'label': _('Search in Customer')
            },
            'stage': {
                'input': 'stage',
                'label': _('Search in Stages')
            },
            'all': {
                'input': 'all',
                'label': _('Search in All')
            },
        }
        searchbar_groupby = {
            'none': {
                'input': 'none',
                'label': _('None')
            },
            'project': {
                'input': 'project',
                'label': _('Project')
            },
        }

        # extends filterby criteria with project the customer has access to
        projects = request.env['project.project'].search([
            # Revamped domain to be based off passed in partner_id
            ('message_partner_ids', 'child_of', partner.commercial_partner_id.id)
        ])
        for project in projects:
            searchbar_filters.update({
                str(project.id): {
                    'label': project.name,
                    'domain': [('project_id', '=', project.id)]
                }
            })

        # extends filterby criteria with project (criteria name is the project id)
        # Note: portal users can't view projects they don't follow
        project_groups = request.env['project.task'].read_group([
            ('project_id', 'not in', projects.ids)
        ], ['project_id'], ['project_id'])
        for group in project_groups:
            proj_id = group['project_id'][0] if group['project_id'] else False
            proj_name = group['project_id'][1] if group['project_id'] else _('Others')
            searchbar_filters.update({
                str(proj_id): {
                    'label': proj_name,
                    'domain': [('project_id', '=', proj_id)]
                }
            })

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain = searchbar_filters[filterby]['domain']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('project.task', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([
                    search_domain,
                    ['|', ('name', 'ilike', search), ('description', 'ilike', search)]
                ])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            if search_in in ('stage', 'all'):
                search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            domain += search_domain

        # task count
        task_count = request.env['project.task'].search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/tasks",
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
                'filterby': filterby,
                'search_in': search_in,
                'search': search
            },
            total=task_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        if groupby == 'project':
            order = "project_id, %s" % order  # force sort on project first to group by project in view

        tasks = request.env['project.task'].search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=(page - 1) * self._items_per_page
        )
        request.session['my_tasks_history'] = tasks.ids[:100]
        if groupby == 'project':
            grouped_tasks = [
                request.env['project.task'].concat(*g)
                for k, g in groupbyelem(tasks, itemgetter('project_id'))
            ]
        else:
            grouped_tasks = [tasks]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'grouped_tasks': grouped_tasks,
            'page_name': 'task',
            'archive_groups': archive_groups,
            'default_url': '/my/tasks',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'partner':
            partner,  # pass partner so when going from other companies records it shows the right company.
        })
        return request.render("project.portal_my_tasks", values)

    @http.route(
        [
            '/my/tasks/create/',
            '/my/companies/<int:partner_id>/tasks/create',
            '/my/contacts/<int:partner_id>/tasks/create',
        ],
        auth='user',
        website=True,
    )
    def create_task(self, partner_id=None, **kw):
        qcontext = request.params.copy()
        partner = request.env['res.partner'].sudo().browse(partner_id)
        if not partner:
            partner = request.env.user.partner_id
        Task = request.env['project.task'].sudo()
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
                    return request.redirect(
                        partner.get_portal_url(record=task)
                    )
                except Exception as e:
                    self._handle_exception(e, qcontext, kw)

        self.prepare_task_vals(
            record=('task', Task),
            partner=partner,
            context=qcontext,
        )
        return request.render('care_center_portal.create_task', qcontext)

    @http.route(
        [
            '/my/task/<int:task_id>',
            '/my/companies/<int:partner_id>/task/<task_id>',
            '/my/contacts/<int:partner_id>/task/<task_id>',
        ],
        type='http',
        auth="public",
        website=True,
    )
    def detail_task(self, task_id, access_token=None, partner_id=None, close_task=False, **kw):
        """
        Override 'portal_my_task' from addons/project/controllers/portal.py to add partner to qcontext & add param
        close_task for user to close ticket.
        @param close_task: Boolean, whether 'close task' was clicked
        """
        response = super().portal_my_task(int(task_id), access_token, **kw)

        partner = request.env['res.partner'].sudo().browse(partner_id)
        if not partner:
            partner = request.env.user.partner_id
        response.qcontext['partner'] = partner

        if close_task:
            try:
                response.qcontext['task'].close_task()
            except Exception as e:
                self._handle_exception(e, response.qcontext, kw)

        return response

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
        self._check_all_mandatory(data, fields, error, error_message)
        self._check_any_mandatory(data, fields, error, error_message)

    def _check_all_mandatory(self, data, fields, error, error_message):
        for field_name in fields.get('all'):
            if not data.get(field_name):
                error[field_name] = 'missing'

        if [err for err in error.values() if err == 'missing']:
            error_message.append('Some required fields are empty.')

    def _check_any_mandatory(self, data, fields, error, error_message):
        any_mandatory = fields.get('any')
        if not any_mandatory:
            return

        for field_name in any_mandatory:
            if not data.get(field_name):
                error[field_name] = 'missing'

        if len([err for err in error.values() if err == 'missing']) == len(any_mandatory):
            error_message.append(
                f'At least one of fields ({", ".join(any_mandatory)}) must be filled out.'
            )
        else:
            error.clear()

    @staticmethod
    def _check_email(data, email, error, error_message):
        """
        Make sure email field is a valid address
        :param data: dict, data common from form POST
        :param error: dict, holding which fields are in an error state
        :param error_message: list->str, holding error messages
        """
        email = data.get(email)
        if email and not tools.single_email_re.match(email):
            error[email] = 'error'
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
            self._check_email(data, fields['email'], error, error_message)
        if check_numeric:
            self._check_numeric(data, fields['numeric'], error, error_message, check_punc)

        return error, error_message

    def task_form_validate(self, data, context):
        form_error, error_message = self._form_validate(
            data,
            {
                'mandatory': {
                    'all': ['name', 'project_id', 'description']
                },
            },
            check_numeric=False,
            check_email=False,
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
