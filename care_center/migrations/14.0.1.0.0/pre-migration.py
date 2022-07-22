from openupgradelib import openupgrade

def update_project_parent_id(cr):
    openupgrade.logged_query(
        cr, """UPDATE project_task
            SET parent_id = parent_task_id
            WHERE parent_task_id IS NOT NULL""")

@openupgrade.migrate(use_env=True)
def migrate(env, version):
    cr = env.cr
    update_project_parent_id(cr)

