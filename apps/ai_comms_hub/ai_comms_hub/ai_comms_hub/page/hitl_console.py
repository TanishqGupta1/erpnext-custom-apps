# Copyright (c) 2025, VisualGraphX and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
	"""Page context for HITL Console"""
	context.no_cache = 1
