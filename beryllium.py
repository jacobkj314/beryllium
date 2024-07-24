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
#TODO add friends table and friends table manipulation functions
def can_view(viewer, poster):
    return viewer != poster #TODO: check permissions

def content(page_url):
    with open(page_url) as page:
        return page.read()

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
        elif self.path == '/comment':
            self.handle_comment_upload()
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

    def serve_html(self, html_content):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))   

    def handle_login_page(self):
        self.serve_html(content("pages/login.html"))
    def handle_signup_page(self):
        self.serve_html(content("pages/signup.html"))

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
        session_id = self.get_session_id()
        current_username = sessions[session_id]["username"]

        html_content = content('pages/main.html')
        
        post_content = content('pages/post.snippet.html')
        
        user_content  = ''
        if current_username in images.keys():
            for post_number, post in enumerate(images[current_username]):
                comments_content = '<ul>'
                for commenter_username, comment_timestamp, comment_text in post["comments"]:
                    comments_content += f"<li>{commenter_username} ({comment_timestamp.strftime('%Y/%m/%d %H:%M:%S')}): {comment_text}</li>"
                comments_content += "</ul>"

                user_content += post_content.replace(
                                                        "<USERNAME/>", 
                                                        current_username
                                           ).replace(
                                                        "<POST_NUMBER/>", 
                                                        str(post_number)
                                           ).replace(
                                                        "<TIMESTAMP/>",
                                                        post["timestamp"].strftime("%Y/%m/%d %H:%M:%S")
                                           ).replace(
                                                        "<FACEIMAGE/>",
                                                        post["images"][0]
                                           ).replace(
                                                        "<AWAYIMAGE/>",
                                                        post["images"][1]
                                           ).replace(
                                                        "<COMMENTS/>",
                                                        comments_content
                                           )

        post_form   = ''
        if current_username not in images.keys(): #TODO - may need a new way of determining whether this message appears - not can_view_page
            post_form += "<p> You must upload before viewing others' images!</p>"
        if current_username not in images.keys(): #TODO: make more advanced logic - can_post
            post_form += content("pages/form.snippet.html")

        other_content = ''
        if current_username in images.keys(): #TODO - can_view_page
            for other_username, other_posts in list(images.items())[::-1]:
                if can_view(current_username, other_username):
                    for post_number, post in enumerate(other_posts):
                        comments_content = '<ul>'
                        for commenter_username, comment_timestamp, comment_text in post["comments"]:
                            comments_content += f"<li>{commenter_username} ({comment_timestamp.strftime('%Y/%m/%d %H:%M:%S')}): {comment_text}</li>"
                        comments_content += "</ul>"
                        other_content += post_content.replace(
                                                                "<USERNAME/>", 
                                                                other_username
                                                    ).replace(
                                                                "<POST_NUMBER/>", 
                                                                str(post_number)
                                                    ).replace(
                                                                "<TIMESTAMP/>",
                                                                post["timestamp"].strftime("%Y/%m/%d %H:%M:%S")
                                                    ).replace(
                                                                "<FACEIMAGE/>",
                                                                post["images"][0]
                                                    ).replace(
                                                                "<AWAYIMAGE/>",
                                                                post["images"][1]
                                                    ).replace(
                                                                "<COMMENTS/>",
                                                                comments_content
                                                    )

        html_content = html_content.replace(
                                                "<USER_POSTS/>", 
                                                user_content
                                  ).replace(
                                                "<POST_FORM/>", 
                                                post_form
                                  ).replace(
                                                "<OTHER_POSTS/>", 
                                                other_content
                                  )
        return self.serve_html(html_content)

    def handle_comment_upload(self):
        global sessions
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = urllib.parse.parse_qs(post_data)
        
        session_id = self.get_session_id()
        current_username = sessions[session_id]["username"]

        if 'poster_username' in parsed_data and 'poster_post' in parsed_data and 'comment_text' in parsed_data:
            poster_username = parsed_data["poster_username"][0]
            poster_post = int(parsed_data["poster_post"][0])
            comment_text = parsed_data["comment_text"][0]
            if poster_username in images.keys() and len(images[poster_username]) > poster_post:
                images[poster_username][poster_post]["comments"].append (
                                                                            (
                                                                                current_username,
                                                                                datetime.now(),
                                                                                comment_text
                                                                            )
                                                                        )
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

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
                images[user_name].append   (
                                            {
                                                "images"    :   [
                                                                    faceImage, 
                                                                    awayImage
                                                                ], 
                                                "timestamp" :   datetime.now(), 
                                                "comments"  :   list()
                                            }
                                        )
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
