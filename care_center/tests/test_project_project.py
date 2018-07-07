from odoo.tests import common


class TestProject(common.TransactionCase):

    def test_alias_name_has_prefix(self):

        Param = self.env['ir.config_parameter']
        prefix = 'support'

        Param.set_param(
            'mail.catchall.alias', prefix,
            groups=['base.group_system'],
        )

        Param.set_param(
            'care_center.alias_name_prefix', True,
            groups=['base.group_system'],
        )

        project = self.env['project.project'].create({
            'name': 'Project with Alias',
        })

        self.assertTrue(project.alias_name.startswith(prefix))
