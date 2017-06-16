# -*- coding: utf-8 -*-


def uninstall_hook(cr, registry):
    # convert priorities to high to avoid inconsistency
    # after the module is uninstalled
    cr.execute("""
        UPDATE project_issue SET priority = '1' WHERE priority IN ('3', '4', '5');
        """
    )
