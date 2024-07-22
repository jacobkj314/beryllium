from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import base64
import os
import http.cookies

# Dummy function to check credentials (replace with real implementation)
def check_credentials(username, password):
    # Verify user credentials
    # # # return username == "admin" and password == "password"
    return True

# Simple in-memory session store
sessions = {}

# # # images
images = {}


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/logout':
            self.handle_logout()
            return

        session_id = self.get_session_id()
        if session_id and session_id in sessions:
            self.handle_main_page()
        else:
            self.handle_login_page()

    def do_POST(self):
        if self.path == '/login':
            self.handle_login()
        else:
            session_id = self.get_session_id()
            if session_id and session_id in sessions:
                self.handle_image_upload()
            else:
                self.handle_login_page()

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

        if username and password and check_credentials(username, password):
            session_id = base64.b64encode(os.urandom(24)).decode('utf-8')
            # # # # # sessions[session_id] = {"username": username, "image": None}
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
        
        # Create an HTML page with stored images and a form for uploading new images
        html_content = """
        <html>
        <body>
            <h1>Upload Image</h1>
        """
        
        session_id = self.get_session_id()
        # # # # # user_data = sessions[session_id]
        user_name = sessions[session_id]["username"]
        
        # # # # # if user_data["image"]:
        if user_name in images.keys():
             # html_content += "<p>You have already uploaded an image:</p>"
            # # # # # html_content += f'<img src="data:image/png;base64,{user_data["image"]}" alt="Your Image" style="width:100%"><br><br>'
            html_content += f'<img src="data:image/png;base64,{images[user_name]}" alt="Your Image" style="width:100%"><br><br>'
            
            html_content += """
            <h2>OTHER PEOPLE'S Images</h2>
            """
            
            # # # # # for session in sessions.values():
            # # # # #     if session["image"]:
            # # # # #         html_content += f'<p>{session["username"]}:</p>'
            # # # # #         html_content += f'<img src="data:image/png;base64,{session["image"]}" alt="Stored Image" style="width:100%"><br><br>'
            for username, image in images.items():
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
                            const base64String = e.target.result.split(',')[1];
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
        # # # # # user_data = sessions[session_id]
        user_name = sessions[session_id]["username"]
        
        # Ensure user can only upload one image
        # # # # # if user_data["image"]:
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
                # # # # # user_data["image"] = new_image
                images[user_name] = new_image
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

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
