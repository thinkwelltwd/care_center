odoo.define('care_center_portal.chatter', function (require) {
'use strict';
    var core = require('web.core');
    var ajax = require('web.ajax');
    var qweb = core.qweb;
    var PortalChatter = require('portal.chatter').PortalChatter;

    PortalChatter.include({

        _loadTemplates: function(){
            return $.when(this._super(), ajax.loadXML('/care_center_portal/static/src/xml/portal_chatter.xml', qweb));
        },
    });

});