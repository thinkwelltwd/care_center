from openupgradelib import openupgrade

def drop_unused_field(env):
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE project_task
        DROP COLUMN parent_task_id""",
    )

@openupgrade.migrate()
def migrate(env, version):
    drop_unused_field(env)

