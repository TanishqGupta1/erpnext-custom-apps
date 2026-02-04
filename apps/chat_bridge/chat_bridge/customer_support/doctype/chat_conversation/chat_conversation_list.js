frappe.listview_settings["Chat Conversation"] = {
	hide_name_column: true,
	onload(listview) {
		listview.page.add_action_item(__("Mine"), () => {
			listview.filter_area.add([[listview.doctype, "assigned_to", "=", frappe.session.user]]);
		});
		listview.page.add_action_item(__("Unassigned"), () => {
			listview.filter_area.add([[listview.doctype, "assigned_to", "is", "not set"]]);
		});
	},
	formatters: {
		status(value) {
			const colors = {
				open: "orange",
				pending: "yellow",
				snoozed: "blue",
				resolved: "green",
				closed: "green",
			};
			const indicator = colors[value?.toLowerCase?.() || "open"] || "gray";
			return `<span class="indicator ${indicator}">${frappe.utils.escape_html(value || "")}</span>`;
		},
	},
};
