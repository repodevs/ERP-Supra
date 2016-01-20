import time
import netsvc
import openerp.exceptions
import decimal_precision as dp
import re
from tools.translate import _
from osv import fields, osv
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

class order_preparation(osv.osv):
	_inherit = "order.preparation"
	_description = "Order Packaging"
	_columns = {
		'sale_id': fields.many2one('sale.order', 'Sale Order', select=True, required=True, readonly=True, domain=[('quotation_state','=', 'win')], states={'draft': [('readonly', False)]}),
		'picking_id': fields.many2one('stock.picking', 'Delivery Order', required=False, domain="[('sale_id','=', sale_id), ('state','not in', ('cancel','done'))]", readonly=True, states={'draft': [('readonly', False)]},track_visibility='always'),
	}

	def sale_change(self, cr, uid, ids, sale):
		if sale:
			res = {}; line = []
			data = self.pool.get('sale.order').browse(cr, uid, sale)
			
			res['poc'] = data.client_order_ref
			res['partner_id'] = data.partner_id.id
			res['duedate'] = data.delivery_date
			res['partner_shipping_id'] = data.partner_shipping_id.id

			for x in data.order_line:
				material_lines=self.pool.get('sale.order.material.line').search(cr,uid,[('sale_order_line_id', '=' ,x.id)])
				for y in self.pool.get('sale.order.material.line').browse(cr, uid, material_lines):

					# Cek Material Line Dengan OP Line
					nilai= 0
					op_line=self.pool.get('order.preparation.line').search(cr,uid,[('sale_line_material_id', '=' ,y.id)])
					for l in self.pool.get('order.preparation.line').browse(cr, uid, op_line):

						# Cek Status OP 
						op=self.pool.get('order.preparation').browse(cr, uid, [l.preparation_id.id])[0]
						if op.state <> 'cancel':
							nilai += l.product_qty

					if nilai < y.qty:
						line.append({
									 'product_id' : y.product_id.id,
									 'product_qty': y.qty - nilai,
									 'product_uom': y.uom.id,
									 'name': y.desc,
									 'sale_line_material_id':y.id
						})

			res['prepare_lines'] = line
			return  {'value': res}


	def preparation_confirm(self, cr, uid, ids, context=None):
		val = self.browse(cr, uid, ids)[0]
		for x in val.prepare_lines:

			nilai= 0
			op_line=self.pool.get('order.preparation.line').search(cr,uid,[('sale_line_material_id', '=' ,x.sale_line_material_id.id)])

			for l in self.pool.get('order.preparation.line').browse(cr, uid, op_line):

				op=self.pool.get('order.preparation').browse(cr, uid, [l.preparation_id.id])[0]
				if op.state <> 'cancel':
					nilai += l.product_qty
			so_material_line=self.pool.get('sale.order.material.line').browse(cr, uid, [x.sale_line_material_id.id])[0]

			mm = ' ' + so_material_line.product_id.default_code + ' '
			msg = 'Product' + mm + 'Melebihi Order.!\n'

			if nilai > so_material_line.qty:
				raise openerp.exceptions.Warning(msg)

		return super(order_preparation, self).preparation_confirm(cr, uid, ids, context=context)
		
order_preparation()

class order_preparation_line(osv.osv):
	_inherit = "order.preparation.line"
	_columns = {
		'sale_line_material_id': fields.many2one('sale.order.material.line', 'Material Ref'),
	}

order_preparation_line()