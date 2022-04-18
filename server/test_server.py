# Multithreading
import math
import fcntl
import struct
import socket
import threading
import itertools
from time import sleep

# Server
import flask

from flask import Blueprint, request, jsonify, render_template, abort
from jinja2 import TemplateNotFound
from flask_socketio import SocketIO, join_room, leave_room

blueprint = Blueprint("blueprint", __name__, url_prefix="/", static_folder="../static")

# Create flask server
app = flask.Flask(__name__, template_folder="templates")
app.debug = True
app.config["DEBUG"] = True
app.config[
    "SEND_FILE_MAX_AGE_DEFAULT"
] = 0  # IMPORTANT disables cacheing of our javascript on requesting computer so printer list will update every time it is requested

socketio = SocketIO()
socketio.init_app(app)

client_dict = {}
rpis_signals = {}
rpis = []
setup_hwid = None
setup_paused = False
setup_finished = False


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


def get_eth_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            return socket.inet_ntoa(
                fcntl.ioctl(s.fileno(), 0x8915, struct.pack("256s", b"eth0"))[20:24]
            )
        except OSError:
            sleep(1)


def layout_nodes(pi_to_pi_strengths, signal_strengths):
    layout = []

    keys = list(signal_strengths.keys())
    for i, key in enumerate(keys):
        if i == 0:
            x = 0
            y = 0
            r = signal_strengths[key]
            layout.append([x, y, r])
        elif i == 1:
            n0_to_n1 = (
                pi_to_pi_strengths[keys[0]][key] + pi_to_pi_strengths[key][keys[0]]
            ) / 2
            x = n0_to_n1
            y = 0
            r = signal_strengths[key]
            layout.append([x, y, r])
        else:
            n0_to_n1 = (
                pi_to_pi_strengths[keys[0]][keys[1]]
                + pi_to_pi_strengths[keys[1]][keys[0]]
            ) / 2
            n0_to_nx = (
                pi_to_pi_strengths[keys[0]][key] + pi_to_pi_strengths[key][keys[0]]
            ) / 2
            n1_to_nx = (
                pi_to_pi_strengths[keys[1]][key] + pi_to_pi_strengths[key][keys[1]]
            ) / 2

            angle = math.acos(
                (n0_to_n1 ** 2 + n0_to_nx ** 2 - n1_to_nx ** 2)
                / (2 * n0_to_n1 * n0_to_nx)
            )
            x = n0_to_nx * math.cos(angle)
            y = n0_to_nx * math.sin(angle)
            r = signal_strengths[key]
            layout.append([x, y, r])

    return layout


def trilateration(points):
    x1 = points[0][0]
    y1 = points[0][1]
    r1 = points[0][2]
    x2 = points[1][0]
    y2 = points[1][1]
    r2 = points[1][2]
    x3 = points[2][0]
    y3 = points[2][1]
    r3 = points[2][2]

    A = 2 * x2 - 2 * x1
    B = 2 * y2 - 2 * y1
    C = r1 ** 2 - r2 ** 2 - x1 ** 2 + x2 ** 2 - y1 ** 2 + y2 ** 2
    D = 2 * x3 - 2 * x2
    E = 2 * y3 - 2 * y2
    F = r2 ** 2 - r3 ** 2 - x2 ** 2 + x3 ** 2 - y2 ** 2 + y3 ** 2
    x = (C * E - F * B) / (E * A - B * D)
    y = (C * D - A * F) / (B * D - A * E)
    return [x, y]


def generate_location(layout):
    combinations = itertools.combinations(layout, 3)
    xs = []
    ys = []
    for comb in combinations:
        location = trilateration(comb)
        x = location[0]
        y = location[1]
        xs.append(x)
        ys.append(y)
    location = sum(xs) / len(xs), sum(ys) / len(ys)
    return location


def update_drawing(pi_to_pi_strengths, signal_strengths, remote_addr):
    layout = layout_nodes(pi_to_pi_strengths, signal_strengths)
    location = generate_location(layout)
    socketio.emit(
        "draw_triangulation",
        {"pis": layout, "location": location},
        namespace="/",
        room=f"{remote_addr}",
    )


@blueprint.route("/")
def home():
    # AUTH stuff
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
        socketio.emit("macs_of_intrest", temp_dict["mac"], namespace="/")
        print(temp_dict)
    except:
        pass

    print(f"Route - home")

    try:
        return render_template("home.html", body=f"")
    except TemplateNotFound:
        print("Template not found")
        return ""
    
@socketio.on("ready", namespace="/")
def ready():
    # room = client_dict[request.remote_addr]["mac"]
    room = request.remote_addr
    join_room(room)
    
    pi_to_pi_strengths = {
        "mac1": {"mac2": -66, "mac3": -66, "mac4": -93},
        "mac2": {"mac1": -66, "mac3": -93, "mac4": -66},
        "mac3": {"mac1": -66, "mac2": -93, "mac4": -66},
        "mac4": {"mac1": -93, "mac2": -66, "mac3": -66},
    }
    signal_strengths = {"mac1": -53, "mac2": -25, "mac3": -66, "mac4": -45}
    update_drawing(pi_to_pi_strengths, signal_strengths, room)

def response_contains_all_pis(lookup_hwid):
    for pi in rpis:
        if pi is not lookup_hwid and pi not in rpis_signals[lookup_hwid]:
            print(f"\tMissing {pi}")
            return False
    return True


def setup_thread():
    print(f"\tScanning {rpis}")
    for pi in rpis:
        socketio.emit("macs_of_intrest", pi, namespace="/")
    for i, pi in enumerate(rpis):
        while True:
            msg = f"\tScanning with {pi} ({i+1}/{len(rpis)})..."
            print(msg)
            socketio.emit("update_text", msg, namespace="/")
            # socketio.emit("monitor_once", namespace="/")
            socketio.emit("monitor_once", namespace="/", room=pi)
            global setup_hwid
            setup_hwid = pi
            global setup_paused
            setup_paused = True
            print("\tWaiting...")
            while setup_paused:
                sleep(0.1)
            print("\tGot response...")
            if response_contains_all_pis(pi):
                print("\tResponse is good!")
                break
    msg = "\tScanning complete!"
    print(msg)
    socketio.emit("update_text", msg, namespace="/")
    global setup_finished
    setup_finished = True
    
    eth_addr = get_eth_ip_address()
    for pi in rpis:
        print(f"\tStarting {pi}...")
        socketio.emit("monitor_continuous", eth_addr, namespace="/", room=pi)
        # socketio.emit("monitor_continuous", eth_addr, namespace="/")


@socketio.on("setup", namespace="/")
def setup():
    thread = threading.Thread(target=setup_thread)
    thread.start()


def process_data(message):
    global setup_paused
    global setup_hwid

    hwid = message["hw"]
    data = message["data"]
    if hwid not in rpis:
        rpis.append(hwid)
    if hwid == setup_hwid:
        setup_paused = False
        setup_hwid = None
    rpis_signals[hwid] = data

    if len(rpis) >= 3 and setup_finished:
    #if len(rpis) >= 3:
        for client in client_dict.values():
            # Mapping
            pi_to_pi_strengths = {}
            for mac in rpis:
                temp_dict = {}
                for mac2 in rpis:
                    if mac is not mac2:
                        temp_dict[mac2] = rpis_signals[mac][mac2]
                pi_to_pi_strengths[mac] = temp_dict

            # Signal stuff
            signal_strengths = {}
            for k in rpis_signals.keys():
                if client['mac'] in rpis_signals[k].keys():
                    signal_strengths[k] = rpis_signals[k][client["mac"]]

            update_drawing(pi_to_pi_strengths, signal_strengths, client["ip"])


@socketio.on("ping", namespace="/")
def receive_ping(message):
    # print(f"Ping: {message}")
    print(f"Ping: {message['ip']}")
    join_room(message["hw"])
    process_data(message)


@socketio.on("data", namespace="/")
def receive_data(message):
    # print(f"Data: {message}")
    try:
        print(f"Data: {message['ip']} Sample: {message['data']['38:f9:d3:26:c9:dd']}")
    except:
        print(f"Data: {message['ip']}")
    join_room(message["hw"])
    process_data(message)



# Run the flask server
app.register_blueprint(blueprint)
app.run(host="0.0.0.0", port=5000)
