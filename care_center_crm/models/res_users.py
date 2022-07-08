from odoo import api, fields, models, modules


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def systray_get_activities(self):
        res = super(ResUsers, self).systray_get_activities()

        query = """
            SELECT count(*),
                CASE
                    WHEN %(today)s::date - phonecall.date::date = 0 Then 'today'
                    WHEN %(today)s::date - phonecall.date::date > 0 Then 'overdue'
                    WHEN %(today)s::date - phonecall.date::date < 0 Then 'planned'
                END AS states
            FROM crm_phonecall AS phonecall
            WHERE (
                    (
                        team_id IN (SELECT team_id FROM team_member_user_rel WHERE user_id = %(user_id)s) 
                        AND user_id IS NULL
                    )
                    OR user_id = %(user_id)s
                )
                AND state IN ('open', 'pending')
            GROUP BY states;
        """
        self.env['crm.phonecall'].flush()
        self.env.cr.execute(query, {
            'today': fields.Date.context_today(self),
            'user_id': self.env.uid,
        })
        phonecall_data = self.env.cr.dictfetchall()

        user_phonecalls = {
            'name': 'Phone Calls to Return',
            'type': 'activity',
            'model': 'crm.phonecall',
            'icon': modules.module.get_module_icon('crm'),
            'total_count': 0,
            'today_count': 0,
            'overdue_count': 0,
            'planned_count': 0,
        }

        for call_type in phonecall_data:
            user_phonecalls['%s_count' % call_type['states']] += call_type['count']
            if call_type['states'] in ('today', 'overdue'):
                user_phonecalls['total_count'] += call_type['count']

        if user_phonecalls['total_count'] or user_phonecalls['planned_count']:
            res.insert(0, user_phonecalls)

        return res
