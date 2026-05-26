from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from onboard import MerchantOnboardingSystem
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the onboarding system
api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Store active sessions (in production, use a database)
sessions = {}

def get_or_create_session(session_id: str) -> MerchantOnboardingSystem:
    """Get existing session or create new one"""
    if session_id not in sessions:
        sessions[session_id] = MerchantOnboardingSystem(api_key)
    return sessions[session_id]

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint for merchant onboarding"""
    try:
        data = request.json
        if not data:
            return jsonify({
                "message": "No data provided",
                "type": "error"
            }), 400
            
        user_input = data.get('message', '')
        session_id = data.get('session_id', 'default')
        action = data.get('action', 'message')
        
        if not user_input:
            return jsonify({
                "message": "Please provide a message",
                "type": "error"
            }), 400
        
        print(f"\n{'='*60}")
        print(f"📨 Session: {session_id}")
        print(f"📝 Message: {user_input}")
        
        # Get or create session
        onboarding = get_or_create_session(session_id)
        
        # Handle different actions
        if action == 'confirm':
            result = onboarding.confirm_onboarding(user_input)
        else:
            result = onboarding.process_input(user_input)
        
        # Ensure the response is clean - only send what's needed
        clean_result = {
            "message": result.get("message", ""),
            "type": result.get("type", "prompt"),
            "onboarding_complete": result.get("onboarding_complete", False)
        }
        
        # Only include extracted_data if onboarding is complete
        if result.get("onboarding_complete"):
            clean_result["backend_payload"] = result.get("backend_payload")
            clean_result["profile"] = result.get("profile")
        
        print(f"✅ Response: {clean_result['type']}")
        return jsonify(clean_result)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "message": "Sorry, I encountered an error. Please try again.",
            "type": "error"
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    """
    Reset the onboarding session
    """
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        
        if session_id in sessions:
            sessions[session_id].reset()
        
        return jsonify({
            "message": "Session reset successfully",
            "type": "system"
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": "error"
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "message": "Merchant Onboarding API is running"
    })

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """
    List active sessions (for debugging)
    """
    return jsonify({
        "active_sessions": len(sessions),
        "session_ids": list(sessions.keys())
    })

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🌟 Merchant Onboarding API starting on port {port}")
    print(f"📡 Health check: http://localhost:{port}/api/health")
    print(f"💬 Chat endpoint: http://localhost:{port}/api/chat")
    
    app.run(host='0.0.0.0', port=port, debug=debug)