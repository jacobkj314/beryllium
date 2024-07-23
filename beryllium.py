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
from hashlib import sha3_512

import sqlite3
db_conn = sqlite3.connect('.db')
db_cursor = db_conn.cursor()
db_cursor.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, passhash TEXT)')
db_conn.commit()

def cryptohash(s:str) -> str:
    if not isinstance(s, str):
        s = ''
    return sha3_512(s.encode('utf-8')).hexdigest()
def add_user(username, passhash):
    db_cursor.execute(f"INSERT INTO users (username, passhash) VALUES ('{username}', '{passhash}')")
    db_conn.commit()
def validate_user(username, password):
    if not re.fullmatch('[A-Za-z0-9_]{1,64}', username):
        return False
    passhash = cryptohash(password)
    del password
    return db_cursor.execute(f"SELECT 1 FROM users WHERE username = '{username}' AND passhash = '{passhash}' LIMIT 1").fetchone() is not None
    return True #TODO account management
#TODO add friends table and friends table manipulation functions

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
        
        if self.path == "/signup":
            self.handle_signup_page()
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
        elif self.path == '/signup':
            self.handle_signup()
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
            <a href="/signup">No account? Sign up here!</a>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))

    def handle_signup_page(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html_content = """
        <html>
        <body>
            <h1>Sign Up</h1>
            <form method="POST" action="/signup">
                Username: <input type="text" name="username"><br><br>
                Password: <input type="password" name="password"><br><br>
                <p>By signing up, you agree that the owners/admins of this Beryllium instance may permanently retain your username and a cryptographic hash of your password. In the future, this Beryllium instance may retain a list of users whose images you would like to view and/or a list of users whom you permit to view your images. No other data shall be maintained permanently. For more details, visit <a href="https://github.com/jacobkj314/beryllium">https://github.com/jacobkj314/beryllium</a>.</p>
                <input type="submit" value="Sign Up">
            </form>
            <a href="/signup">Already have an account? Sign in here!</a>
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

        if validate_user(username, password):
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
            self.wfile.write('Invalid credentials. Please <a href="/login">try again</a>.'.encode('utf-8'))
    def handle_signup(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = urllib.parse.parse_qs(post_data)
        
        username = parsed_data.get('username', [None])[0]
        if not re.fullmatch('[A-Za-z0-9_]{1,64}', username):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write('Invalid username. Username may only contain alphanumeric characters and underscores. Please <a href="/signup">try again</a>.'.encode('utf-8'))
            return
        if db_cursor.execute(f"SELECT 1 FROM users WHERE username = '{username}' LIMIT 1").fetchone() is not None:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f'Username "{username}" is already taken. Please <a href="/signup">try again</a>.'.encode('utf-8'))
            return
        password = parsed_data.get('password', [None])[0]
        passhash = cryptohash(password)
        del password
        add_user(username, passhash)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

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

            html_content += f'<p>{user_name}:</p>'

            for post in images[user_name]:

                html_content += f'<img src="data:image/png;base64,{post["images"][0]}" alt="Your Image" style="width:50%">'
                html_content += f'<img src="data:image/png;base64,{post["images"][1]}" alt="Your Image" style="width:50%"><br><br>'
            
            html_content += """
            <h2>OTHER PEOPLE'S Images</h2>
            """
            
            for username, user_content in list(images.items())[::-1]:
                if username != user_name:
                    for user_post in user_content:
                        user_images = user_post["images"]
                        face_image, away_image = user_images

                        html_content += f'<p>{username}:</p>'
                        html_content += f'<img src="data:image/png;base64,{face_image}" alt="Stored Image" style="width:50%">'
                        html_content += f'<img src="data:image/png;base64,{away_image}" alt="Stored Image" style="width:50%"><br><br>'
        else:
            html_content += """
            <p>You must upload before you can see other people's images!</p>
            <form id="uploadForm" method="POST">
                Face Image: <input type="file" id="faceInput" accept="image/*"><br><br>
                Away Image: <input type="file" id="awayInput" accept="image/*"><br><br>
                
                <p> By uploading, you agree that the owners/admins of this Beryllium instance may retain a copy of your images until tomorrow, when the server resets. Your images are never saved to permanent storage (such as a hard drive). If you would like to keep a copy of your images, be sure to save it locally or access Beryllium using an application designed to archive your images. For more details, visit <a href="https://github.com/jacobkj314/beryllium">https://github.com/jacobkj314/beryllium</a>.</p>

                <input type="submit" value="Upload Images">
            </form>
            <script>
                document.getElementById('uploadForm').onsubmit = function(event) {
                    event.preventDefault();
                    const faceFile = document.getElementById('faceInput').files[0];
                    const awayFile = document.getElementById('awayInput').files[0];
                    if (faceFile && awayFile) {
                        function resizeImage(file, callback) {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                const img = new Image();
                                img.onload = function() {
                                    const MAX_SIZE = 600 * 1024; // 600 KB
                                    const canvas = document.createElement('canvas');
                                    const ctx = canvas.getContext('2d');
                                    let width = img.width;
                                    let height = img.height;
                                    
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
                                            callback(event.target.result.split(',')[1]);
                                        };
                                        resizedReader.readAsDataURL(blob);
                                    }, 'image/jpeg', 0.85); // Adjust quality here (0.85 is just an example)
                                };
                                img.src = e.target.result;
                            };
                            reader.readAsDataURL(file);
                        }

                        resizeImage(faceFile, function(faceBase64) {
                            resizeImage(awayFile, function(awayBase64) {
                                const xhr = new XMLHttpRequest();
                                xhr.open('POST', '/', true);
                                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                                xhr.onload = function() {
                                    if (xhr.status === 200) {
                                        window.location.reload();
                                    }
                                };
                                const data = 'faceImage=' + encodeURIComponent(faceBase64) + '&awayImage=' + encodeURIComponent(awayBase64);
                                xhr.send(data);
                            });
                        });
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
        
        if 'faceImage' in parsed_data and 'awayImage' in parsed_data:
            faceImage = parsed_data['faceImage'][0]
            awayImage = parsed_data['awayImage'][0]
            # Validate if they are proper Base64 strings
            try:
                base64.b64decode(faceImage)
                base64.b64decode(awayImage)
                if user_name not in images.keys():
                    images[user_name] = []
                images[user_name].append({"images": [None, None], "comments":list()})
                images[user_name][-1]["images"][0] = faceImage
                images[user_name][-1]["images"][1] = awayImage
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
