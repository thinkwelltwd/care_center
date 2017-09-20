from odoo.models import api, BaseModel


@api.model
def get_form_window_action(self):
    """
    Get Form Action so we can append the action=<id> to URLs,
    so that then navigation menu can be displayed.

    Order by ID Descending, thinking that the newest form view
    is the one the user most likely expects
    """

    return self.env['ir.actions.act_window'].search([
        ('res_model', '=', self.get_access_action()['res_model']),
        ('view_mode', 'ilike', 'form'),
        ('search_view_id', '!=', False),
    ], order="id DESC")



@api.model
def generate_url(self):
    """
    Build the URL to the record's form view, so we can use it in templates.

      - Base URL + Database Name + Record ID + Model Name

    :param self: any Odoo record browse object (with access to env, _cr, and _model)
    :return: string with url
    """
    self.ensure_one()
    base_url = self.env['ir.config_parameter'].get_param('web.base.url')

    action = self.get_access_action()
    action['base_url'] = base_url

    url = "{base_url}/web?#id={res_id}&view_type=form&model={res_model}".format(**action)

    action = self.get_form_window_action()
    if action:
        return '{url}&action={id}'.format(url=url, id=action[0].id)

    return url


BaseModel.generate_url = generate_url
BaseModel.get_form_window_action = get_form_window_action
