from flask import Flask, render_template, redirect, url_for, request
import logging
import socket

hans_addr = 'localhost'
hans_port = 9999
app = Flask(__name__)


def clickCount():
    clickCount.clicks += 1
    if(clickCount.clicks == 16):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto('solo', (hans_addr, hans_port))
        clickCount.clicks = 0
        logging.info('SOLO sent')

clickCount.clicks = 0


@app.route('/', methods=['POST', 'GET'])
def index():
    msg = request.args.get('reply')
    if msg is None:
        msg = ""
    client = request.remote_addr
    return render_template('index.html', ip=client, reply=msg)


@app.route('/hanssolo', methods=['POST'])
def hanssolo():
    # hs = request.form['hanssolo']
    logging.info('HANSSOLO clicked')
    clickCount()
    msg = "Wait for the magic!"
    return redirect(url_for('index', reply=msg))


if __name__ == '__main__':
    logging.basicConfig(filename='hans-server.log',
                        format='%(asctime)s: %(message)s',
                        datefmt='%Y-%m-%d %I:%M:%S',
                        level=logging.INFO)
    logging.info('HANS-WEB started')
    app.run(host='0.0.0.0')
