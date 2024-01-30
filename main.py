from flask import Flask,redirect,request,jsonify,session
import requests,urllib.parse
from datetime import datetime
import json
import snowflake.connector

with open('credentials.json','r') as f:
    creds=json.load(f)
    CLIENT_ID=creds.get('client_id')
    CLIENT_SECRETS=creds.get('client_secret')
    ARTIST_ID=creds.get('artist_id')

app = Flask(__name__)
app.secret_key='kjdkjfkdjss3434efndkjfndjkfnk332'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
    return "Welcome to spotify! please <a href='/login'>login here</a>"

@app.route('/login')
def login():

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope' : 'user-read-private user-read-email',
        'show_dialog': False
    }
    querystring = f'{AUTH_URL}?{urllib.parse.urlencode(params)}'
    return redirect(querystring)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({'errors': request.args['error']})
    
    if 'code' in request.args:        
        data= {
            'code': request.args['code'],
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRETS
       }
    response = requests.post(url=TOKEN_URL,data=data)

    token_info = response.json()

    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token']
    session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

    #return redirect('/playlist')
    return redirect('/artist')

@app.route('/playlist')
def get_playlist():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() >  session['expires_at']:
        print('token_expired, fetching new token...')
        return redirect('/refresh-token')

    headers = {
        'Authorization' : f"Bearer {session['access_token']}"
    }
    response = requests.get(API_BASE_URL+'me',headers=headers)
    playlist = response.json()
    with open(f'myprofile{(datetime.now().strftime("%Y%m%d%H%M%S"))}.json','w') as f:
        json.dump(playlist,f)
        with snowflake.connector.connect() as conn:
            with conn.cursor() as cur:
                print(cur.execute("INSERT INTO PLAYLIST_LOGS VALUES (f)").fetchall())
    return jsonify(playlist)

@app.route('/artist')
def get_artist():

    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() >  session['expires_at']:
        print('token_expired, fetching new token...')
        return redirect('/refresh-token')


    headers = {
        'Authorization' : f"Bearer {session['access_token']}"
    }
    artist_response = requests.get(API_BASE_URL+f'artists/{ARTIST_ID}/albums',headers=headers)
    return jsonify(artist_response.json())

@app.route('/refresh-token')
def refresh_token():

    if refresh_token not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        data = {
            'client_id': CLIENT_ID,
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token']
        }
    response = requests.post(TOKEN_URL,data=data)
    new_token_info= response.json
    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp()+ new_token_info['expires_in']

    return redirect('/playlist')

if __name__ == '__main__':
    app.run(host = '0.0.0.0',debug=True)