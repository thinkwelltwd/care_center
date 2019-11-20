def migrate(cr, version):
    """Convert timesheet_ready_to_invoice to temporary_invoice_status"""
    if not version:
        return
    cr.execute(
        """
    ALTER TABLE account_analytic_line 
    ADD COLUMN temporary_invoice_status text
    """
    )
    cr.execute(
        """
    UPDATE account_analytic_line 
    SET temporary_invoice_status = 'ready' 
    WHERE timesheet_ready_to_invoice is true
    """
    )
    cr.execute(
        """
    UPDATE account_analytic_line 
    SET temporary_invoice_status = 'notready' 
    WHERE timesheet_ready_to_invoice is false
    """
    )
