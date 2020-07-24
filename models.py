# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import csv
from datetime import date as dt
import logging

_logger = logging.getLogger(__name__)


class ProductUploadOrderpoints(models.Model):
    _name = 'product.upload.orderpoints'
    _description = 'product.upload.orderpoints'

    def btn_process(self):
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.product_file:
            raise ValidationError('Debe seleccionar el archivo')
        if self.state != 'draft':
            raise ValidationError('Archivo procesado!')
        self.file_content = base64.decodestring(self.product_file)
        lines = self.file_content.split('\n')
        i = 0
        for line in lines:
            if i < 1:
                i = i + 1
                continue
            lista = line.split(self.delimiter)
            if len(lista) == 6:
                default_code = lista[0]
                location = lista[1]
                minimum = float(lista[2])
                maximum = float(lista[3])
                supplier = lista[4]
                min_qty = float(lista[5])
                warehouse_id = self.env['stock.warehouse'].search([])
                supplier_id = self.env['res.partner'].search([('ref','=',supplier)])
                location_id = self.env['stock.location'].search([('complete_name','=',location)])
                product_id = self.env['product.product'].search([('default_code','=',default_code)],limit=1)
                if product_id and location_id and supplier:
                    vals = {
                            'product_id': product_id.id,
                            'location_id': location_id.id,
                            'warehouse_id': warehouse_id.id,
                            'product_min_qty': minimum,
                            'product_max_qty': maximum,
                            'file_id': self.id,
                            }
                    order_point = self.env['stock.warehouse.orderpoint'].search([('product_id','=',product_id.id),('location_id','=',location_id.id)])
                    if not order_point:
                        return_id = self.env['stock.warehouse.orderpoint'].create(vals)
                    else:
                        order_point.write({'active': False})
                        return_id = self.env['stock.warehouse.orderpoint'].create(vals)
                    vals_supplier = {
                            'product_id': product_id.id,
                            'product_name': product_id.display_name,
                            'name': supplier_id.id,
                            'min_qty': min_qty,
                            'file_id': self.id,
                            }
                    suppinfo = self.env['product.supplierinfo'].search([('product_id','=',product_id.id),('name','=',supplier_id.id)])
                    if not suppinfo:
                        return_id = self.env['product.supplierinfo'].create(vals_supplier)
                    else:
                        suppinfo.write(vals_supplier)

                else:
                    not_processed_content = self.not_processed_content or '' + line or '' + '\n'
                    self.not_processed_content = not_processed_content
            else:
                not_processed_content = self.not_processed_content or '' + line or '' + '\n'
                self.not_processed_content = not_processed_content

        self.state = 'processed'

    name = fields.Char('Nombre')
    product_file = fields.Binary('Archivo')
    delimiter = fields.Char('Delimitador',default=",")
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    file_content = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    order_point_ids = fields.One2many(comodel_name='stock.warehouse.orderpoint',inverse_name='file_id',string='Puntos de pedido')
    supplierinfo_ids = fields.One2many(comodel_name='product.supplierinfo',inverse_name='file_id',string='Proveedores')

class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    file_id = fields.Many2one('product.upload.orderpoints',string='Archivo')

class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    file_id = fields.Many2one('product.upload.orderpoints',string='Archivo')
