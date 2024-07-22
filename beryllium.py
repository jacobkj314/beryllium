#TODO:
# - fill out the api under BerylliumHTTPRequestHandler
# - move big html chunks to separate files
# - compress images before uploading (handle this in js script)
# - USER ACCOUNTS / login management / adding friends
# - Captions and comments

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import base64
import os
import http.cookies
import json
from datetime import datetime
import re

def check_credentials(username, password):
    return True #TODO account management

sessions = {} # Simple in-memory session store

images = {} # # # images structure

last_reset_time = datetime.now()
def check_needs_reset():
    global last_reset_time, images
    now = datetime.now()
    intended_last_reset_time = datetime(now.year, now.month, now.day, 12, 0, 0, 0) #TODO : have a better and more varied function to determine when the server resets
    if now > intended_last_reset_time and not last_reset_time > intended_last_reset_time: 
        images = {}
        last_reset_time = now

class BerylliumHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        check_needs_reset()

        if self.path.startswith('/api'):
            self.handle_api()
            return

        if self.path == '/logout':
            self.handle_logout()
            return

        session_id = self.get_session_id()
        if session_id and session_id in sessions:
            self.handle_main_page()
        else:
            self.handle_login_page()

    def do_POST(self):
        check_needs_reset()

        if self.path == '/login':
            self.handle_login()
        else:
            session_id = self.get_session_id()
            if session_id and session_id in sessions:
                self.handle_image_upload()
            else:
                self.handle_login_page()

    def handle_api(self):
        session_id = self.get_session_id()
        if not session_id and session_id in sessions:
            self.send_response(401)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            json_content = json.dumps({})
            self.wfile.write(json_content.encode('utf-8'))
            return
        
        self.send_response(200)
        self.send_header("Content-type", "text/json")
        self.end_headers()
        
        api_url = re.sub('^/api/?', '', self.path)

        if api_url == '':
            content = images
        elif api_url in images.keys():
            content = images[api_url]
        else:
            content = {}
        json_content = json.dumps(content)
        self.wfile.write(json_content.encode('utf-8'))

    def handle_login_page(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html_content = """
        <html>
        <body>
            <h1>Login</h1>
            <form method="POST" action="/login">
                Username: <input type="text" name="username"><br><br>
                Password: <input type="password" name="password"><br><br>
                <input type="submit" value="Login">
            </form>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))

    def handle_login(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = urllib.parse.parse_qs(post_data)
        
        username = parsed_data.get('username', [None])[0]
        password = parsed_data.get('password', [None])[0]

        if check_credentials(username, password):
            session_id = base64.b64encode(os.urandom(24)).decode('utf-8')
            sessions[session_id] = {"username": username}
            self.send_response(302)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', f'session_id={session_id}; Path=/')
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write("Invalid credentials. Please try again.".encode('utf-8'))

    def handle_logout(self):
        session_id = self.get_session_id()
        if session_id and session_id in sessions:
            del sessions[session_id]
        self.send_response(302)
        self.send_header('Location', '/')
        self.send_header('Set-Cookie', 'session_id=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT')
        self.end_headers()

    def handle_main_page(self):
        global sessions, images
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html_content = """
        <html>
        <body>
            <h1>BERYLLIUM</h1>
        """
        
        session_id = self.get_session_id()
        user_name = sessions[session_id]["username"]
        
        if user_name in images.keys():

            html_content += f'<img src="data:image/png;base64,{images[user_name]}" alt="Your Image" style="width:100%"><br><br>'
            
            html_content += """
            <h2>OTHER PEOPLE'S Images</h2>
            """
            
            for username, image in list(images.items())[::-1]:
                if username != user_name:
                    html_content += f'<p>{username}:</p>'
                    html_content += f'<img src="data:image/png;base64,{image}" alt="Stored Image" style="width:100%"><br><br>'
        else:
            html_content += """
            <p>You must upload before you can see other people's images!</p>
            <form id="uploadForm" method="POST">
                <input type="file" id="fileInput" accept="image/*"><br><br>
                <input type="submit" value="Upload Image">
            </form>
            <script>
                document.getElementById('uploadForm').onsubmit = function(event) {
                    event.preventDefault();
                    const fileInput = document.getElementById('fileInput');
                    const file = fileInput.files[0];
                    if (file) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const img = new Image();
                            img.onload = function() {
                                const MAX_SIZE = 600 * 1024; // 600 KB
                                const canvas = document.createElement('canvas');
                                const ctx = canvas.getContext('2d');
                                let width = img.width;
                                let height = img.height;

                                // Calculate the scaling factor to resize the image
                                let scaleFactor = Math.sqrt(MAX_SIZE / file.size);
                                if (scaleFactor > 1) {
                                    scaleFactor = 1;
                                }

                                canvas.width = width * scaleFactor;
                                canvas.height = height * scaleFactor;

                                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                                canvas.toBlob(function(blob) {
                                    const resizedReader = new FileReader();
                                    resizedReader.onload = function(event) {
                                        const base64String = event.target.result.split(',')[1];
                                        const xhr = new XMLHttpRequest();
                                        xhr.open('POST', '/', true);
                                        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                                        xhr.onload = function() {
                                            if (xhr.status === 200) {
                                                window.location.reload();
                                            }
                                        };
                                        xhr.send('image=' + encodeURIComponent(base64String));
                                    };
                                    resizedReader.readAsDataURL(blob);
                                }, 'image/jpeg', 0.85); // Adjust quality here (0.85 is just an example)
                            };
                            img.src = e.target.result;
                        };
                        reader.readAsDataURL(file);
                    }
                };
            </script>
            """

        

        
        
        html_content += """
            <br><a href="/logout">Logout</a>
        </body>
        </html>
        """
        
        self.wfile.write(html_content.encode('utf-8'))

    def handle_image_upload(self):
        global sessions
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = urllib.parse.parse_qs(post_data)
        
        session_id = self.get_session_id()
        user_name = sessions[session_id]["username"]
        
        # Ensure user can only upload one image
        if user_name in images.keys():
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("You have already uploaded an image.".encode('utf-8'))
            return
        
        # Assuming image is sent in a 'image' field
        if 'image' in parsed_data:
            new_image = parsed_data['image'][0]
            # Validate if it's a proper Base64 string
            try:
                base64.b64decode(new_image)
                images[user_name] = new_image #TODO: this should also create a list to hold comments
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write("Invalid Base64 string.".encode('utf-8'))
                return
        
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.handle_main_page()

    def get_session_id(self):
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            cookies = http.cookies.SimpleCookie(cookie_header)
            if 'session_id' in cookies:
                return cookies['session_id'].value
        return None

def run(server_class=HTTPServer, handler_class=BerylliumHTTPRequestHandler, port=7074):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
