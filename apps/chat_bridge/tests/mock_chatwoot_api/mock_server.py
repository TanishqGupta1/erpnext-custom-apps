"""
Mock Chatwoot API Server for Testing
Simulates Chatwoot API endpoints for isolated development and testing
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from ERPNext

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

# In-memory storage for testing (simulates Chatwoot database)
contacts_db = {}
conversations_db = {}
messages_db = {}
next_contact_id = 1
next_conversation_id = 1
next_message_id = 1

def load_fixture(filename):
    """Load JSON fixture file"""
    filepath = os.path.join(FIXTURES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def save_fixture(filename, data):
    """Save data to fixture file"""
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    filepath = os.path.join(FIXTURES_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize with fixture data if available
def init_fixtures():
    """Load initial test data from fixtures"""
    global contacts_db, conversations_db, messages_db
    global next_contact_id, next_conversation_id, next_message_id
    
    contacts = load_fixture('contacts.json')
    if contacts and 'payload' in contacts:
        for contact in contacts['payload']:
            contacts_db[contact['id']] = contact
            next_contact_id = max(next_contact_id, contact['id'] + 1)
    
    conversations = load_fixture('conversations.json')
    if conversations and 'payload' in conversations:
        for conv in conversations['payload']:
            conversations_db[conv['id']] = conv
            next_conversation_id = max(next_conversation_id, conv['id'] + 1)
    
    # Load messages for conversations
    for conv_id in conversations_db.keys():
        messages = load_fixture(f'conversation_{conv_id}_messages.json')
        if messages and 'payload' in messages:
            messages_db[conv_id] = messages['payload']
        else:
            messages_db[conv_id] = []

init_fixtures()

@app.route('/api/v1/accounts/<account_id>/account', methods=['GET'])
def get_account(account_id):
    """Get account details"""
    return jsonify({
        'id': int(account_id),
        'name': 'Test Account',
        'domain': 'test.localhost',
        'support_email': 'support@test.localhost',
        'created_at': datetime.now().isoformat()
    })

@app.route('/api/v1/accounts/<account_id>/contacts', methods=['GET'])
def get_contacts(account_id):
    """List all contacts"""
    contacts = list(contacts_db.values())
    return jsonify({
        'payload': contacts,
        'meta': {
            'current_page': 1,
            'per_page': 20,
            'total_pages': 1,
            'total_count': len(contacts)
        }
    })

@app.route('/api/v1/accounts/<account_id>/contacts/<contact_id>', methods=['GET'])
def get_contact(account_id, contact_id):
    """Get a specific contact"""
    contact_id = int(contact_id)
    if contact_id in contacts_db:
        return jsonify(contacts_db[contact_id])
    return jsonify({'error': 'Contact not found'}), 404

@app.route('/api/v1/accounts/<account_id>/contacts', methods=['POST'])
def create_contact(account_id):
    """Create a new contact"""
    global next_contact_id
    data = request.get_json()
    
    contact = {
        'id': next_contact_id,
        'name': data.get('name', ''),
        'email': data.get('email'),
        'phone_number': data.get('phone_number'),
        'identifier': data.get('identifier'),
        'avatar_url': data.get('avatar_url'),
        'custom_attributes': data.get('custom_attributes', {}),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    contacts_db[next_contact_id] = contact
    next_contact_id += 1
    
    return jsonify(contact), 201

@app.route('/api/v1/accounts/<account_id>/contacts/<contact_id>', methods=['PUT'])
def update_contact(account_id, contact_id):
    """Update a contact"""
    contact_id = int(contact_id)
    if contact_id not in contacts_db:
        return jsonify({'error': 'Contact not found'}), 404
    
    data = request.get_json()
    contact = contacts_db[contact_id]
    
    # Update fields
    if 'name' in data:
        contact['name'] = data['name']
    if 'email' in data:
        contact['email'] = data['email']
    if 'phone_number' in data:
        contact['phone_number'] = data['phone_number']
    if 'custom_attributes' in data:
        contact['custom_attributes'].update(data['custom_attributes'])
    
    contact['updated_at'] = datetime.now().isoformat()
    
    return jsonify(contact)

@app.route('/api/v1/accounts/<account_id>/contacts/search', methods=['GET'])
def search_contacts(account_id):
    """Search contacts"""
    query = request.args.get('q', '').lower()
    contacts = [c for c in contacts_db.values() 
                if query in c.get('name', '').lower() 
                or query in c.get('email', '').lower()
                or query in c.get('phone_number', '').lower()]
    
    return jsonify({
        'payload': contacts,
        'meta': {
            'current_page': 1,
            'per_page': 20,
            'total_pages': 1,
            'total_count': len(contacts)
        }
    })

@app.route('/api/v1/accounts/<account_id>/conversations', methods=['GET'])
def get_conversations(account_id):
    """List all conversations"""
    conversations = list(conversations_db.values())
    
    # Apply filters
    status = request.args.get('status')
    inbox_id = request.args.get('inbox_id')
    
    filtered = conversations
    if status:
        filtered = [c for c in filtered if c.get('status') == status]
    if inbox_id:
        filtered = [c for c in filtered if c.get('inbox_id') == int(inbox_id)]
    
    return jsonify({
        'payload': filtered,
        'meta': {
            'current_page': 1,
            'per_page': 20,
            'total_pages': 1,
            'total_count': len(filtered)
        }
    })

@app.route('/api/v1/accounts/<account_id>/conversations/<conversation_id>', methods=['GET'])
def get_conversation(account_id, conversation_id):
    """Get a specific conversation"""
    conversation_id = int(conversation_id)
    if conversation_id in conversations_db:
        conv = conversations_db[conversation_id].copy()
        # Add messages
        conv['messages'] = messages_db.get(conversation_id, [])
        return jsonify(conv)
    return jsonify({'error': 'Conversation not found'}), 404

@app.route('/api/v1/accounts/<account_id>/conversations/<conversation_id>', methods=['PUT'])
def update_conversation(account_id, conversation_id):
    """Update conversation status or assignment"""
    conversation_id = int(conversation_id)
    if conversation_id not in conversations_db:
        return jsonify({'error': 'Conversation not found'}), 404
    
    data = request.get_json()
    conv = conversations_db[conversation_id]
    
    if 'status' in data:
        conv['status'] = data['status']
    if 'assignee_id' in data:
        conv['assignee'] = {'id': data['assignee_id']}
    
    conv['updated_at'] = datetime.now().isoformat()
    
    return jsonify(conv)

@app.route('/api/v1/accounts/<account_id>/conversations/<conversation_id>/messages', methods=['GET'])
def get_messages(account_id, conversation_id):
    """Get messages for a conversation"""
    conversation_id = int(conversation_id)
    messages = messages_db.get(conversation_id, [])
    
    return jsonify({
        'payload': messages,
        'meta': {
            'current_page': 1,
            'per_page': 50,
            'total_pages': 1,
            'total_count': len(messages)
        }
    })

@app.route('/api/v1/accounts/<account_id>/conversations/<conversation_id>/messages', methods=['POST'])
def create_message(account_id, conversation_id):
    """Send a message in a conversation"""
    global next_message_id
    conversation_id = int(conversation_id)
    
    if conversation_id not in conversations_db:
        return jsonify({'error': 'Conversation not found'}), 404
    
    data = request.get_json()
    
    message = {
        'id': next_message_id,
        'content': data.get('content', ''),
        'message_type': data.get('message_type', 'outgoing'),
        'content_type': data.get('content_type', 'text'),
        'content_attributes': data.get('content_attributes', {}),
        'private': data.get('private', False),
        'created_at': datetime.now().isoformat(),
        'sender': {
            'id': 1,
            'name': 'Test Agent',
            'email': 'agent@test.localhost'
        }
    }
    
    if conversation_id not in messages_db:
        messages_db[conversation_id] = []
    messages_db[conversation_id].append(message)
    next_message_id += 1
    
    # Update conversation last_activity_at
    conversations_db[conversation_id]['last_activity_at'] = datetime.now().isoformat()
    
    return jsonify(message), 201

@app.route('/api/v1/accounts/<account_id>/inboxes', methods=['GET'])
def get_inboxes(account_id):
    """List all inboxes"""
    return jsonify({
        'payload': [
            {
                'id': 1,
                'name': 'Website',
                'channel_type': 'Channel::WebWidget',
                'created_at': datetime.now().isoformat()
            }
        ]
    })

@app.route('/api/v1/accounts/<account_id>/labels', methods=['GET'])
def get_labels(account_id):
    """List all labels"""
    return jsonify({
        'payload': [
            {'id': 1, 'title': 'urgent', 'description': 'Urgent conversations'},
            {'id': 2, 'title': 'vip', 'description': 'VIP customers'}
        ]
    })

@app.route('/api/v1/accounts/<account_id>/teams', methods=['GET'])
def get_teams(account_id):
    """List all teams"""
    return jsonify({
        'payload': [
            {'id': 1, 'name': 'Support Team', 'description': 'Customer support team'}
        ]
    })

# Error simulation endpoints for testing
@app.route('/api/v1/accounts/<account_id>/test/401', methods=['GET'])
def test_401(account_id):
    """Simulate 401 Unauthorized"""
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/api/v1/accounts/<account_id>/test/429', methods=['GET'])
def test_429(account_id):
    """Simulate 429 Rate Limit"""
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.route('/api/v1/accounts/<account_id>/test/503', methods=['GET'])
def test_503(account_id):
    """Simulate 503 Service Unavailable"""
    return jsonify({'error': 'Service unavailable'}), 503

if __name__ == '__main__':
    print("Starting Mock Chatwoot API Server on http://0.0.0.0:3001")
    print("Fixtures directory:", FIXTURES_DIR)
    app.run(host='0.0.0.0', port=3001, debug=True)

