# OPS API Integration Module
# Whitelisted methods for OnPrintShop GraphQL API calls

import frappe
import requests
import json
from datetime import datetime, timedelta

def get_settings():
    settings = frappe.get_doc("OPS API Settings")
    if not settings.enabled:
        frappe.throw("OPS API is not enabled")
    return settings

def get_access_token():
    settings = get_settings()
    if settings.access_token and settings.token_expires:
        if isinstance(settings.token_expires, str):
            expires = datetime.strptime(settings.token_expires, "%Y-%m-%d %H:%M:%S")
        else:
            expires = settings.token_expires
        if expires > datetime.now() + timedelta(minutes=5):
            return settings.access_token
    
    token_url = settings.api_url.replace("/graphql", "/oauth/token")
    response = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": settings.client_id,
        "client_secret": settings.get_password("client_secret")
    }, timeout=settings.timeout or 30)
    response.raise_for_status()
    token_data = response.json()
    
    settings.access_token = token_data.get("access_token")
    settings.token_expires = datetime.now() + timedelta(hours=24)
    settings.last_token_request = datetime.now()
    settings.connection_status = "Connected"
    settings.last_successful_call = datetime.now()
    settings.last_error = ""
    settings.save(ignore_permissions=True)
    frappe.db.commit()
    return settings.access_token

def execute_graphql(query, variables=None):
    settings = get_settings()
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(settings.api_url, headers=headers, json=payload, timeout=settings.timeout or 30)
    response.raise_for_status()
    result = response.json()
    
    frappe.db.set_value("OPS API Settings", "OPS API Settings", "last_successful_call", datetime.now())
    frappe.db.set_value("OPS API Settings", "OPS API Settings", "connection_status", "Connected")
    
    if "errors" in result:
        frappe.throw(f"GraphQL Error: {json.dumps(result['errors'])}")
    return result.get("data")

@frappe.whitelist()
def test_connection():
    try:
        token = get_access_token()
        return {"success": True, "message": "Connected"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_master_option_tags():
    gql = """query { getMasterOptionTag { masterOptionTag { master_option_tag_id master_option_tag_name } totalMasterOptionTag } }"""
    return execute_graphql(gql)

@frappe.whitelist()
def sync_master_option_tags():
    ops_data = get_master_option_tags()
    ops_tags = ops_data.get("getMasterOptionTag", {}).get("masterOptionTag", [])
    synced = 0
    created = 0
    for tag in ops_tags:
        tag_id = tag.get("master_option_tag_id")
        tag_name = tag.get("master_option_tag_name")
        existing = frappe.db.get_value("OPS Master Option Tag", {"ops_tag_id": tag_id}, "name")
        if existing:
            frappe.db.set_value("OPS Master Option Tag", existing, "tag_name", tag_name)
            synced += 1
        else:
            doc = frappe.get_doc({"doctype": "OPS Master Option Tag", "ops_tag_id": tag_id, "tag_name": tag_name})
            doc.insert(ignore_permissions=True)
            created += 1
    frappe.db.commit()
    return {"synced": synced, "created": created, "total": len(ops_tags)}
