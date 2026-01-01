from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime

class GrokAPIHandler(BaseHTTPRequestHandler):
    # Store conversation history per session
    sessions = {}
    
    def _set_headers(self, content_type='application/json', status=200):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/health':
            self._set_headers()
            response = {
                'status': 'healthy',
                'service': 'Grok AI via Puter.js',
                'timestamp': datetime.now().isoformat(),
                'active_sessions': len(self.sessions)
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self._set_headers(status=404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/api/chat':
                self._handle_chat(data)
            elif self.path == '/api/reset':
                self._handle_reset(data)
            else:
                self._set_headers(status=404)
                self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode())
                
        except Exception as e:
            self._set_headers(status=500)
            error_response = {
                'success': False,
                'error': str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def _handle_chat(self, data):
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        reset = data.get('reset', False)
        
        if not message:
            self._set_headers(status=400)
            self.wfile.write(json.dumps({'error': 'Message is required'}).encode())
            return
        
        # Initialize or reset session
        if reset or session_id not in self.sessions:
            self.sessions[session_id] = []
        
        history = self.sessions[session_id]
        
        self._set_headers('text/html')
        
        # Create HTML page that executes Puter.js and returns result
        html_response = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://js.puter.com/v2/"></script>
    <style>
        body {{
            font-family: monospace;
            padding: 20px;
            background: #1e1e1e;
            color: #00ff00;
        }}
        #result {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
    </style>
</head>
<body>
    <div id="status">⏳ Processing your request...</div>
    <pre id="result"></pre>
    <script>
        let conversationHistory = {json.dumps(history)};
        
        async function processChat() {{
            try {{
                const userMessage = {json.dumps(message)};
                const sessionId = {json.dumps(session_id)};
                
                // Add user message to history
                conversationHistory.push({{
                    role: "user",
                    content: userMessage
                }});

                document.getElementById('status').textContent = '🤖 Grok is thinking...';

                // Call Grok AI via Puter.js
                const response = await puter.ai.chat(conversationHistory, {{
                    model: 'x-ai/grok-4.1-fast'
                }});

                // Add assistant response to history
                conversationHistory.push({{
                    role: "assistant",
                    content: response.message.content
                }});

                // Prepare result
                const result = {{
                    success: true,
                    session_id: sessionId,
                    message: userMessage,
                    response: response.message.content,
                    conversation_length: conversationHistory.length,
                    timestamp: new Date().toISOString()
                }};
                
                document.getElementById('status').textContent = '✅ Complete!';
                document.getElementById('result').textContent = JSON.stringify(result, null, 2);
                
                // Store updated history
                fetch('/api/store-history', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        session_id: sessionId,
                        history: conversationHistory
                    }})
                }});
                
            }} catch (error) {{
                const errorResult = {{
                    success: false,
                    error: error.message,
                    timestamp: new Date().toISOString()
                }};
                document.getElementById('status').textContent = '❌ Error occurred';
                document.getElementById('result').textContent = JSON.stringify(errorResult, null, 2);
            }}
        }}
        
        // Start processing
        processChat();
    </script>
</body>
</html>
        '''
        self.wfile.write(html_response.encode())
    
    def _handle_reset(self, data):
        session_id = data.get('session_id', 'default')
        
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        self._set_headers()
        response = {
            'success': True,
            'message': f'Session {session_id} reset successfully',
            'timestamp': datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        # Custom logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def run(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, GrokAPIHandler)
    
    print("=" * 60)
    print("🚀 GROK AI SERVER VIA PUTER.JS")
    print("=" * 60)
    print(f"🌐 Server running on: http://localhost:{port}")
    print(f"❤️  Health check: http://localhost:{port}/health")
    print(f"💬 Chat endpoint: POST http://localhost:{port}/api/chat")
    print(f"🔄 Reset endpoint: POST http://localhost:{port}/api/reset")
    print("=" * 60)
    print("\n📦 Request Body Example:")
    print(json.dumps({
        "message": "Hello, Grok!",
        "session_id": "user123",
        "reset": False
    }, indent=2))
    print("\n🛑 Press Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped gracefully")
        httpd.shutdown()

if __name__ == '__main__':
    run()