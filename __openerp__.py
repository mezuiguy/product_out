{
    'name': 'Sortie Materiel',
    'version': '1.0',
    'category': 'Inventory',
    'sequence': 15,
    'summary': 'Bon de sortie materiel',
    'description': """
    """,
    'depends': ['stock','project'],
    'data': [
	         'product_out_sequence.xml',
             'product_out_view.xml',
             ],
    'demo':[],
    'installable': True,
    'auto_install': False,
    'application': False,
}
