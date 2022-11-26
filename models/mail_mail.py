# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import base64
import datetime
import logging
import psycopg2
import smtplib
import threading
import re
import pytz

from collections import defaultdict
from dateutil.parser import parse

from odoo import _, api, fields, models
from odoo import tools
from odoo.addons.base.models.ir_mail_server import MailDeliveryException

_logger = logging.getLogger(__name__)

class MailMail(models.Model):
    _inherit = 'mail.mail'

    ## OVERRIDE METHOD SEND FOR OUTLOOK, THE ERROR THAT MAILS ARE NOT SENT IF YOU ARE NOT THE ADMIN USER IS SOLVED
    def send(self, auto_commit=False, raise_exception=False):
        """ Sends the selected emails immediately, ignoring their current
            state (mails that have already been sent should not be passed
            unless they should actually be re-sent).
            Emails successfully delivered are marked as 'sent', and those
            that fail to be deliver are marked as 'exception', and the
            corresponding error mail is output in the server logs.
            :param bool auto_commit: whether to force a commit of the mail status
                after sending each mail (meant only for scheduler processing);
                should never be True during normal transactions (default: False)
            :param bool raise_exception: whether to raise an exception if the
                email sending process has failed
            :return: True
        """
        for mail_server_id, smtp_from, batch_ids in self._split_by_mail_configuration():
            smtp_session = None
            
            if self.env.company.email:
                smtp_from = self.env.company.email

            try:
                smtp_session = self.env['ir.mail_server'].connect(mail_server_id=mail_server_id, smtp_from=smtp_from)
            except Exception as exc:
                if raise_exception:
                    # To be consistent and backward compatible with mail_mail.send() raised
                    # exceptions, it is encapsulated into an Odoo MailDeliveryException
                    raise MailDeliveryException(_('Unable to connect to SMTP Server'), exc)
                else:
                    batch = self.browse(batch_ids)
                    batch.write({'state': 'exception', 'failure_reason': exc})
                    batch._postprocess_sent_message(success_pids=[], failure_type="mail_smtp")
            else:
                self.browse(batch_ids)._send(
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    smtp_session=smtp_session)
                _logger.info(
                    'Sent batch %s emails via mail server ID #%s',
                    len(batch_ids), mail_server_id)
            finally:
                if smtp_session:
                    smtp_session.quit()