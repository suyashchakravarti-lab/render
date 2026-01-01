from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

class PuterGrokHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>Grok AI via Puter.js</title>
    <script src="https://js.puter.com/v2/"></script>
</head>
<body>
    <h1>Grok AI Integration</h1>
    <div id="output"></div>
    
    <script>
        let conversationHistory = [];

        async function chat(userMessage) {
            conversationHistory.push({
                role: "user",
                content: userMessage
            });

            const response = await puter.ai.chat(conversationHistory, {
                model: 'x-ai/grok-4.1-fast'
            });

            conversationHistory.push({
                role: "assistant",
                content: response.message.content
            });

            return response.message.content;
        }

        async function resetConversation() {
            conversationHistory = [];
            return "Conversation reset";
        }

        // API endpoint for external calls
        window.grokAPI = {
            chat: chat,
            reset: resetConversation,
            getHistory: () => conversationHistory
        };

        // Listen for messages from parent window or API calls
        window.addEventListener('message', async (event) => {
            if (event.data.action === 'chat') {
                try {
                    const response = await chat(event.data.message);
                    event.source.postMessage({
                        success: true,
                        response: response,
                        history: conversationHistory
                    }, event.origin);
                } catch (error) {
                    event.source.postMessage({
                        success: false,
                        error: error.message
                    }, event.origin);
                }
            } else if (event.data.action === 'reset') {
                resetConversation();
                event.source.postMessage({
                    success: true,
                    response: "Conversation reset"
                }, event.origin);
            }
        });

        document.getElementById('output').innerHTML = '<p>✅ Grok AI ready! Waiting for requests...</p>';
    </script>
</body>
</html>
            '''
            self.wfile.write(html_content.encode())
            
        elif self.path.startswith('/api/chat'):
            # Parse query parameters
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            message = params.get('message', [''])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Return HTML that will execute the chat and post back result
            api_html = f'''
<!DOCTYPE html>
<html>
<head>
    <script src="https://js.puter.com/v2/"></script>
</head>
<body>
    <pre id="result">Processing...</pre>
    <script>
        let conversationHistory = JSON.parse(localStorage.getItem('grok_history') || '[]');
        
        async function processChat() {{
            const userMessage = {json.dumps(message)};
            
            conversationHistory.push({{
                role: "user",
                content: userMessage
            }});

            const response = await puter.ai.chat(conversationHistory, {{
                model: 'x-ai/grok-4.1-fast'
            }});

            conversationHistory.push({{
                role: "assistant",
                content: response.message.content
            }});
            
            localStorage.setItem('grok_history', JSON.stringify(conversationHistory));

            const result = {{
                success: true,
                response: response.message.content,
                conversationLength: conversationHistory.length
            }};
            
            document.getElementById('result').textContent = JSON.stringify(result, null, 2);
        }}
        
        processChat();
    </script>
</body>
</html>
            '''
            self.wfile.write(api_html.encode())
        
        elif self.path == '/api/reset':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            reset_html = '''
<!DOCTYPE html>
<html>
<body>
    <pre id="result">Resetting...</pre>
    <script>
        localStorage.removeItem('grok_history');
        document.getElementById('result').textContent = JSON.stringify({
            success: true,
            message: "Conversation history cleared"
        }, null, 2);
    </script>
</body>
</html>
            '''
            self.wfile.write(reset_html.encode())

def run(server_class=HTTPServer, handler_class=PuterGrokHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'🚀 Server running on http://localhost:{port}')
    print(f'📡 Chat API: http://localhost:{port}/api/chat?message=YOUR_MESSAGE')
    print(f'🔄 Reset API: http://localhost:{port}/api/reset')
    print(f'🌐 Web Interface: http://localhost:{port}/')
    httpd.serve_forever()

if __name__ == '__main__':
    run()