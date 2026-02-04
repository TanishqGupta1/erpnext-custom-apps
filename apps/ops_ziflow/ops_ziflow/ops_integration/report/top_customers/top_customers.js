// Copyright (c) 2025, Visual Graphx
// License: MIT

frappe.query_reports["Top Customers"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 0
        },
        {
            "fieldname": "limit",
            "label": __("Top N"),
            "fieldtype": "Int",
            "default": 10
        }
    ]
};
