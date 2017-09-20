.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
Care Center Mattermost
======================

This module adds basic Mattermost 4.1+ integration, where messages can be sent via email templates.
The template must have an outgoing server specified, and the server specified must be a
Mattermost server.

At this point, attachments are not supported.

Usage
=====
Configure Mattermost Server settings by going to Technical / Outgoing Email Servers. Enter
Mattermost URL / Port info there, skipping Email-related settings. To use this server for sending
Mattermost messages, go to an Email Template / Advanced Settings tab, and enter this server
in the Outgoing Mail Server tab.

Create `Personal Access Tokens <https://docs.mattermost.com/developer/personal-access-tokens.html>`_
on the Mattermost server and add those tokens in the Mattermost tab of Odoo Contacts.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/thinkwell/care_center/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======


Contributors
------------

* Dave Burkholder <dave@thinkwelldesigns.com>


Maintainer
----------

This module is maintained by Thinkwell Designs.
