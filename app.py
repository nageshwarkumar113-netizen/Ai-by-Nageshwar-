import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
import openai

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# In-memory storage for conversations (production में database use करें)
conversations = {}

@app.route('/')
def home():
    """Homepage - chat interface"""
    if 'user_id' not in session:
        session['user_id'] = os.urandom(16).hex()
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for sending messages"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        user_id = session.get('user_id')
        
        # Initialize conversation history if not exists
        if user_id not in conversations:
            conversations[user_id] = []
        
        # Add user message to history
        conversations[user_id].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get AI response from OpenAI
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{'role': msg['role'], 'content': msg['content']} 
                         for msg in conversations[user_id]],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_message = response['choices'][0]['message']['content']
            
            # Add AI response to history
            conversations[user_id].append({
                'role': 'assistant',
                'content': ai_message,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'response': ai_message,
                'conversation_id': user_id
            })
        
        except openai.error.APIError as e:
            return jsonify({'error': f'OpenAI API Error: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Server Error: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history"""
    user_id = session.get('user_id')
    if user_id in conversations:
        return jsonify({'history': conversations[user_id]})
    return jsonify({'history': []})

@app.route('/api/clear', methods=['POST'])
def clear_chat():
    """Clear conversation history"""
    user_id = session.get('user_id')
    if user_id in conversations:
        conversations[user_id] = []
    return jsonify({'success': True, 'message': 'Chat cleared'})

@app.route('/api/new-chat', methods=['POST'])
def new_chat():
    """Start a new chat"""
    session['user_id'] = os.urandom(16).hex()
    return jsonify({'success': True, 'conversation_id': session['user_id']})

if __name__ == '__main__':
    app.run(debug=True, port=5000)