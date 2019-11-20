def uninstall_hook(cr, registry):
    # convert priorities to high to avoid inconsistency
    # after the module is uninstalled
    cr.execute(
        """
        UPDATE project_task SET priority = '0' WHERE priority like '1';
        UPDATE project_task SET priority = '1' WHERE priority IN ('2', '3', '4', '5');
        """
    )
