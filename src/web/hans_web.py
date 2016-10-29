
from flask import Flask, render_template, redirect, url_for, request, jsonify

app = Flask(__name__)
#app.config['SERVER_NAME'] = 'hansmusic:5000'

@app.route('/', methods=['POST', 'GET'])
def index():
    msg = request.args.get('reply')
    if msg is None:
        msg = ""
    client = request.remote_addr
    return render_template('index.html', ip=client, reply=msg)

@app.route('/hanssolo', methods=['POST'])
def hanssolo():
    #hs = request.form['hanssolo']
    clickCount()
    msg = "Wait for the magic!"
    return redirect(url_for('index', reply = msg))

def clickCount():
    clickCount.clicks += 1
    if(clickCount.clicks == 5):        
        print(5) # ITT MEHET KI A SOCKET
        clickCount.clicks = 0
clickCount.clicks = 0

if __name__ == '__main__':
    #app.config['SERVER_NAME'] = 'hansmusic:5000'
    app.run(debug=True, host='0.0.0.0')