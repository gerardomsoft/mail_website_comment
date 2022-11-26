# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID, Command

_logger = logging.getLogger(__name__)

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        res = super(MailThread, self)._message_auto_subscribe_followers(updated_values, default_subtype_ids)
        if self._name == "sale.order":
            return []
        else:
            return res
    

        