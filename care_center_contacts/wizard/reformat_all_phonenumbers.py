from odoo import models


class ReformatAllPhonenumbers(models.TransientModel):
    _inherit = "reformat.all.phonenumbers"

    def run_reformat_all_phonenumbers(self):
        res = super().run_reformat_all_phonenumbers()

        extra_numbers = self.env['extra.contactinfo'].search([('type', '!=', 'email')])

        for number in extra_numbers:
            new_phone = number.phone_format(number.name)
            if number.name != new_phone:
                number.write({'name': new_phone})

        return res
