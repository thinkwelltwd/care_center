from odoo import models, api


class PhoneCommon(models.AbstractModel):
    _inherit = 'phone.common'
    _description = 'Common methods for phone features'

    @api.model
    def get_record_from_phone_number(self, presented_number):
        res = super().get_record_from_phone_number(presented_number)
        if res:
            return res

        nr_digits_to_match_from_end = \
            self.env.company.number_of_digits_to_match_from_end
        if len(presented_number) >= nr_digits_to_match_from_end:
            end_number_to_match = presented_number[
                -nr_digits_to_match_from_end:len(presented_number)]
        else:
            end_number_to_match = presented_number

        sql = """
        SELECT res_partner.id, res_partner.display_name FROM res_partner 
        INNER JOIN extra_contactinfo
        ON res_partner.id = extra_contactinfo.partner_id
        WHERE
        extra_contactinfo.type != 'email' AND
        extra_contactinfo.name ILIKE %s
        LIMIT 1;
        """
        self._cr.execute(sql, ('%{}'.format(end_number_to_match),))
        result = self._cr.fetchall()

        if not result:
            return False

        partner_id, display_name = result[0]
        return ('res.partner', partner_id, display_name)
