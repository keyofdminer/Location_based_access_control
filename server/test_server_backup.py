# Multithreading
import fcntl
import struct
import socket
import threading
from time import sleep

# Server
import flask

from flask import request, jsonify, render_template
from flask_socketio import SocketIO


# Create flask server
app = flask.Flask(__name__, static_url_path="", static_folder="")
app.debug = True
app.config["DEBUG"] = True
app.config[
    "SEND_FILE_MAX_AGE_DEFAULT"
] = 0  # IMPORTANT disables cacheing of our javascript on requesting computer so printer list will update every time it is requested

socketio = SocketIO()
socketio.init_app(app)

client_dict = {}
signal_dict = {}

authaction=None
clientip=None
gatewayname=None
tok=None
redir=None

js_code = "<script>\nvar Reload = function(){\nwindow.location.reload();\n}\nwindow.onload = function(){\nsetTimeout(Reload, 1000);\n}\n</script>"

def get_eth_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            return socket.inet_ntoa(
                fcntl.ioctl(s.fileno(), 0x8915, struct.pack("256s", b"eth0"))[20:24]
            )
        except OSError:
            sleep(1)

def get_leases():
    f = open("/var/lib/misc/dnsmasq.leases", "r")
    lines = f.readlines()
    f.close()
    leases = {}
    for line in lines:
        mac = line.split(" ")[1]
        ip = line.split(" ")[2]
        leases[ip] = mac
    return leases

@app.route("/")
def home():
    # "GET /?authaction=http://192.168.0.1:2050/opennds_auth/?clientip=192.168.0.51&gatewayname=openNDS&tok=2b083c1a&redir=http%3a%2f%2fcaptive.apple.com%2fhots>
    try:
        leases = get_leases()
        temp_dict = {}
        temp_dict["authaction"] = request.args.get("authaction")
        temp_dict["ip"] = request.remote_addr
        temp_dict["mac"] = leases[request.remote_addr]
        temp_dict["gatewayname"] = request.args.get("gatewayname")
        temp_dict["tok"] = request.args.get("tok")
        temp_dict["redir"] = request.args.get("redir")
        client_dict[f"{request.remote_addr}"] = temp_dict
    except:
        pass
    tri_dict = {}
    for k in signal_dict.keys():
        if temp_dict["mac"] in signal_dict[k].keys():
            tri_dict[k] = signal_dict[k][temp_dict["mac"]]
    print(f"Route - home")
    return f"{temp_dict} {tri_dict} {js_code}"


@socketio.on("data", namespace="/")
def receive_data(message):
    signal_dict[message["hw"]] = message["data"]
    print(message)


@socketio.on("ping", namespace="/")
def receive_ping(message):
    print(message)
    socketio.emit("monitor_continuous", get_eth_ip_address(), namespace="/", room=request.sid)
    # socketio.emit("monitor_once", namespace="/", room=request.sid)

# Run the flask server
app.run(host="0.0.0.0", port=5000)


# Notes:
# When we get a ping, get the request.sid. This will allow us to emit only to that node
# We will also get the associated MAC and IP
#
# When a setup command is run, cycle between each regestered sid and monitor once.
# Lookup and average each path length between pair of registered nodes in their corrisponding monitor data.

# Use this data as the distance between each node
