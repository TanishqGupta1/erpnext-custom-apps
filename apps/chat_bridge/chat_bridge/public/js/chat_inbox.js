frappe.pages["chatwoot-inbox"].on_page_load = function () {
	frappe.set_route("conversations");
	frappe.show_alert({
		message: __("Chat Inbox has moved to the Conversations page."),
		indicator: "blue",
	});
};
