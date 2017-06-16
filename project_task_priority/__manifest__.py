# -*- coding: utf-8 -*-

{
    "name": "Project Task Priority",
    "summary": "Adds all priority levels found in project_issue_priority",
    "version": "10.0.1.0.0",
    "author": "Dave Burkholder <dave@thinkwelldesigns.com>",
    "license": "AGPL-3",
    "category": "Project Management",
    "depends": ["project"],
    "data": [
        'views/project_task.xml',
    ],
    "installable": True,
    "uninstall_hook": "uninstall_hook"
}
