def migrate(cr, version):
    """Remove SO Line from AAL when not invoiceable"""
    if not version:
        return
    cr.execute(
        """
    UPDATE account_analytic_line 
    SET so_line=NULL 
    WHERE invoice_status='notinvoiceable' AND so_line IS NOT NULL;

    UPDATE account_analytic_line
    SET so_line=NULL 
    WHERE task_id IN (SELECT id FROM project_task WHERE is_invoiceable = 'no')
    AND so_line IS NOT NULL 
    AND invoice_status!='invoiced';
    """
    )
