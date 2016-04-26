# -*- coding: utf-8 -*-

from openerp import models, fields, api

class skillset(models.Model):
    _name = 'skillset.skillset'

    name = fields.Char(string="Key Skill")
    active=fields.Boolean(string="Active",default=True)

    _sql_constraints = [
    	('name_uniq', 'unique(name)','Skills name must be unique!'),
    ]

