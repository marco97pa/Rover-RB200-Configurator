# COSE DA FARE:
# - Selezionare audio MF

import requests
from http.client import RemoteDisconnected
from urllib3.exceptions import ProtocolError
from requests.exceptions import ConnectionError, Timeout, ChunkedEncodingError
import webbrowser
import re
import time
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from tkinter import Toplevel, Label, Button
import sys, os
from pysnmp.hlapi import *
import threading

VERSION = "1.8"
owner = "marco97pa"  # Repository owner's username
repo = "Rover-RB200-Configurator"  # Repository name

# Initialize the flags
updating = False
machine = ""

class MUX:
    def __init__(self, name, ol, pol, freq, symb, ISI):
        self.name = name
        self.ol = ol
        self.pol = pol
        self.freq = freq
        self.symb = symb
        self.ISI = ISI

    def __str__(self):
        return f"ol: {self.ol}, pol: {self.pol}, freq: {self.freq}, symb: {self.symb}, ISI: {self.ISI}"

# Creazione dell'oggetto con i valori specificati
muxR = MUX("MUX MR10", "10600", "HH", "12535.500", "35294", "4")
muxA = MUX("MUX A", "10600", "VH", "12606.000", "35294", "4")
muxB = MUX("MUX B", "10600", "VH", "12606.000", "35294", "5")
muxMF = MUX("Servizi MF", "10600", "HH", "12627.000", "35294", "2")

# Lista di oggetti MUX
mux_list = [muxR, muxA, muxB, muxMF]
mux_DVBT = [muxR.name, muxA.name, muxB.name]
mux_MF = [muxMF.name]

# Funzione per cercare un MUX per nome
def search_mux_by_name(name):
    for mux in mux_list:
        if mux.name == name:
            return mux
    return None

# Funzione per cercare un MUX per frequenza e ISI
def search_mux_by_freq_and_ISI(freq, ISI):
    for mux in mux_list:
        if str( float(mux.freq) ) + " MHz" == freq and mux.ISI == ISI:
            return mux.name
    return "NON RICONOSCIUTO"

# Function to get the latest release version from GitHub
def get_latest_release_version(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        release_info = response.json()
        return release_info['tag_name'], release_info['html_url']
    else:
        return None, None

# Function to show the custom alert with version information
def show_version_info():
    current_version = VERSION
    latest_version, latest_url = get_latest_release_version(owner, repo) 

    if latest_version:
        update_button_state = tk.NORMAL if current_version != latest_version else tk.DISABLED

        # Create a custom dialog window
        dialog = Toplevel(root)
        dialog.title("Informazioni")

        Label(dialog, text="Realizzato da Marco Fantauzzo, Salvatore Chillura e Giovanni Gaetani").pack(pady=5)

        # Load and display the image
        image_url = "https://www.raiway.it/static/media/logo.74640e43.png"  # Logo Rai Way dal sito
        image = Image.open(requests.get(image_url, stream=True).raw)

        # Calculate the new size while maintaining the aspect ratio
        max_size = (100, 100)
        image.thumbnail(max_size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        image_label = Label(dialog, image=photo)
        image_label.image = photo  # Keep a reference to avoid garbage collection
        image_label.pack(pady=5)

        Label(dialog, text="Versione installata:").pack(pady=5)
        Label(dialog, text=current_version).pack(pady=5)
        Label(dialog, text="Ultima versione:").pack(pady=5)
        Label(dialog, text=latest_version).pack(pady=5)

        update_button = Button(dialog, text="Aggiorna", state=update_button_state, command=lambda: update_app(latest_url))
        update_button.pack(pady=10)

        Button(dialog, text="Chiudi", command=dialog.destroy).pack(pady=5)
    else:
        tk.messagebox.showerror("Errore", "Non sei connesso a Internet, riprova")

# Function to handle the update action
def update_app(latest_url):
    if latest_url:
        webbrowser.open(latest_url)
    else:
        tk.messagebox.showerror("Errore", "Non riesco a trovare la nuova versione")



def get_status(IP):
    snmp_data = get_snmp_data(IP)
    return snmp_data["Bitrate"], snmp_data["Frequency"], snmp_data["Level"], snmp_data["SNR"], snmp_data["ISI"]
    
def get_snmp_data(ip_address):
    community = 'public'  # Replace with your SNMP community string
    oids = {
        '.1.3.6.1.4.1.19324.2.3.3.3.17.1.7.1':'Bitrate',
        '.1.3.6.1.4.1.19324.2.3.3.3.3.0': 'Frequency',
        '.1.3.6.1.4.1.19324.2.3.3.2.14.1.2.1': 'ISI',
        '.1.3.6.1.4.1.19324.2.3.3.3.4.0': 'Level',
        '.1.3.6.1.4.1.19324.2.3.3.3.5.0': 'SNR'
    }

    results = {}

    for oid, name in oids.items():
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community),
                   UdpTransportTarget((ip_address, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )

        if errorIndication:
            results[name] = str(errorIndication)
        elif errorStatus:
            results[name] = '%s at %s' % (errorStatus.prettyPrint(),
                                          errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
        else:
            for varBind in varBinds:
                value = varBind[1].prettyPrint()
                if name == "Frequency":
                    value = str( float(value)/1000 ) + " MHz"
                elif name == "Level":
                    value = str( float(value)/10 ) + " dBuV"
                elif name == "SNR":
                    value = str( float(value)/10 ) + " dB"
                elif name == "Bitrate":
                    value = str( float(value)/1000000 ) + " Mb/s"

                results[name] = value

    return results

def get_service_list(ip_address):
    community = 'public'  # Replace with your SNMP community string
    oids = [
        '.1.3.6.1.4.1.19324.2.3.6.2.12.1.2.1',
        '.1.3.6.1.4.1.19324.2.3.6.2.12.1.2.2',
        '.1.3.6.1.4.1.19324.2.3.6.2.12.1.2.3',
        '.1.3.6.1.4.1.19324.2.3.6.2.12.1.2.4',
        '.1.3.6.1.4.1.19324.2.3.6.2.12.1.2.5'
    ]

    results = ""

    for oid in oids:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community),
                   UdpTransportTarget((ip_address, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )

        if errorIndication:
            results = str(errorIndication)
        elif errorStatus:
            results = '%s at %s' % (errorStatus.prettyPrint(),
                                          errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
        else:
            for varBind in varBinds:
                results = results + varBind[1].prettyPrint() + ", "
    
    results = "...".join(results.rsplit(", ", 1))
    return results

def get_service_audio(ip_address):
    community = 'public'  # Replace with your SNMP community string
    oid = ".1.3.6.1.4.1.19324.2.3.8.3.2.0"
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((ip_address, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(oid)))
    )

    if errorIndication:
        result = str(errorIndication)
    elif errorStatus:
        result = '%s at %s' % (errorStatus.prettyPrint(),
                                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
    else:
        for varBind in varBinds:
            value = varBind[1].prettyPrint()
            oid = ".1.3.6.1.4.1.19324.2.3.8.2.3.1.2." + value
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                        CommunityData(community),
                        UdpTransportTarget((ip_address, 161)),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid)))
            )
            if errorIndication:
                result = str(errorIndication)
            elif errorStatus:
                result = '%s at %s' % (errorStatus.prettyPrint(),
                                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
            else:
                for varBind in varBinds:
                    value = varBind[1].prettyPrint()
                    result = value

    return result

def get_machine(ip_address):
    community = 'public'  # Replace with your SNMP community string
    oid = ".1.3.6.1.4.1.19324.101.0"
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((ip_address, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(oid)))
    )

    if errorIndication:
        name = str(errorIndication)
    elif errorStatus:
        name = '%s at %s' % (errorStatus.prettyPrint(),
                                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
    else:
        for varBind in varBinds:
            value = varBind[1].prettyPrint()
            name = value
    
    oid = ".1.3.6.1.4.1.19324.2.3.1.1.3.0"
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((ip_address, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(oid)))
    )

    if errorIndication:
        version = str(errorIndication)
    elif errorStatus:
        version = '%s at %s' % (errorStatus.prettyPrint(),
                                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
    else:
        for varBind in varBinds:
            value = varBind[1].prettyPrint()
            version = value

    return name, version
    
def check_bitrate(data):
    try:
        # Split the string and take the first part
        number_str = data.split()[0]
        # Convert the string to a float
        number_float = float(number_str)
        
        if "RSR 100" in machine:
            # Check if the value is between 6 and 8
            if 6 <= number_float <= 8:
                return True
            else:
                return False
        else:
            # Check if the value is between 18 and 38
            if 18 <= number_float <= 38:
                return True
            else:
                return False
    except (ValueError, IndexError):
        print("Error: The string does not match the expected format or is not a number.")
        return False

def set_ISI(IP, ISI):
    # URL for the GET request
    url = "http://" + IP + "/conf_sat.html?11=" + ISI
    max_retries = 15
    attempts = 0
    
    while attempts < max_retries:
        try:
            # Send the GET request
            response = requests.get(url)
            # Print the response status code and content
            print(f"ISI: Status Code: {response.status_code}")
            break  # Exit the loop if the request is successful
        except (RemoteDisconnected, ProtocolError, ConnectionError, ChunkedEncodingError) as e:
            attempts += 1
            print(f"Error: {e}. Retrying... ({attempts}/{max_retries})")
            if attempts == max_retries:
                print("Max retries reached. Exiting.")
                break

def set_PLS(IP):
    # URL for the GET request
    url = "http://" + IP + "/conf_sat.html?16=0&17=131070&18=262140"
    max_retries = 15
    attempts = 0
    
    while attempts < max_retries:
        try:
            # Send the GET request
            response = requests.get(url)
            # Print the response status code and content
            print(f"PLS: Status Code: {response.status_code}")
            break  # Exit the loop if the request is successful
        except (RemoteDisconnected, ProtocolError, ConnectionError,ChunkedEncodingError) as e:
            attempts += 1
            print(f"Error: {e}. Retrying... ({attempts}/{max_retries})")
            if attempts == max_retries:
                print("Max retries reached. Exiting.")
                break

def set_Profile(IP, profile):
    # URL for the GET request
    url = "http://" + IP + "/conf_sys.html?270=Load+Profile+" + profile
    max_retries = 15
    attempts = 0
    
    while attempts < max_retries:
        try:
            # Send the GET request
            response = requests.get(url)
            # Print the response status code and content
            print(f"Set Profile: Status Code: {response.status_code}")
            break  # Exit the loop if the request is successful
        except (RemoteDisconnected, ProtocolError, ConnectionError,ChunkedEncodingError) as e:
            attempts += 1
            print(f"Error: {e}. Retrying... ({attempts}/{max_retries})")
            if attempts == max_retries:
                print("Max retries reached. Exiting.")
                break

def gateway(ip_address):
    # Split the IP address into its components
    parts = ip_address.split('.')
    
    # Replace the last part with '1'
    parts[-1] = '1'
    
    # Join the parts back together
    modified_ip = '.'.join(parts)
    
    return modified_ip


def set_NTP(IP, NTP):
    # URL for the GET request
    url = "http://" + IP + "/conf_sys.html?267=NTP&258=" + NTP + "&259=1+h"
    max_retries = 15
    attempts = 0
    
    while attempts < max_retries:
        try:
            # Send the GET request
            response = requests.get(url)
            # Print the response status code and content
            print(f"Set NTP: Status Code: {response.status_code}")
            break  # Exit the loop if the request is successful
        except (RemoteDisconnected, ProtocolError, ConnectionError,ChunkedEncodingError) as e:
            attempts += 1
            print(f"Error: {e}. Retrying... ({attempts}/{max_retries})")
            if attempts == max_retries:
                print("Max retries reached. Exiting.")
                break

def set_IP(IP, NewIP):
    # URL for the GET request
    url = "http://" + IP + "/conf_sys.html?244=" + NewIP + "&245=255.255.255.000&246=" + gateway(NewIP)
    max_retries = 5
    attempts = 0
    
    while attempts < max_retries:
        try:
            # Send the GET request
            response = requests.get(url)
            # Print the response status code and content
            print(f"Set IP: Status Code: {response.status_code}")
            break  # Exit the loop if the request is successful
        except (RemoteDisconnected, ProtocolError, ConnectionError,ChunkedEncodingError) as e:
            attempts += 1
            print(f"Error: {e}. Retrying... ({attempts}/{max_retries})")
            if attempts == max_retries:
                print("Max retries reached. Exiting.")
                break

def set_RX(IP, ol, freq, pol, symb, profile):
    # URL for the GET request
    url = "http://" + IP + "/conf_sat.html?2=" + ol + "+MHz&5=DVB-S2&9=Auto+Symbolrate&3=" + freq + "+MHz&6=" + pol + "&7=OFF&8=0+dB&4=" + symb + "+kS%2Fs&15=Loop&10=MIS&61=AUTO&270=Save+as+Profile+" + profile + ""
    print(url)
    
    max_retries = 15
    attempts = 0
    timeout_seconds = 7 
    
    while attempts < max_retries:
        try:
            # Send the GET request
            response = requests.get(url, timeout=timeout_seconds)
            # Print the response status code and content
            print(f"Params set: Status Code: {response.status_code}")
            break  # Exit the loop if the request is successful
        except (RemoteDisconnected, ProtocolError, ConnectionError, ChunkedEncodingError) as e:
            attempts += 1
            print(f"Error: {e}. Retrying... ({attempts}/{max_retries})")
            if attempts == max_retries:
                print("Max retries reached. Exiting.")
                break
        except Timeout as e:
            print("OK: Device not responding, probably rebooting")
            break


def is_valid_ip(ip):
    # Regular expression for validating an IPv4 address
    ipv4_pattern = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    
    match = re.match(r'^https?://([^/]+)', ip)
    if match:
        ip = match.group(1)
        inputIP.delete(0, tk.END)  # Clear the current value
        inputIP.insert(0, ip)  # Insert the new value

    if ipv4_pattern.match(ip):
        return True
    else:
        return False

def on_closing():
    # Gracefully close
    if updating:
        toggle_update()
    print("Window is closing")
    root.destroy()
    root.after(100, os._exit, 0)  # Delay the exit slightly

# Create the main window
root = tk.Tk()
root.title("ROVER Configurator - ver. " + VERSION)
root.protocol("WM_DELETE_WINDOW", on_closing)
if getattr(sys, 'frozen', False):
    root.iconbitmap(os.path.join(sys._MEIPASS, "icon.ico"))
else:
    root.iconbitmap("icon.ico") 

# Function to launch webpage
def webpage():
    IP = inputIP.get()
    if is_valid_ip(IP):
        webbrowser.open("http://" + IP)

def update_services():
    global updating
    if updating:
        IP = inputIP.get()
        if "RSR 100" in machine:
            labelServices.config(text = "Servizio: " + get_service_audio(IP))
        else:
            labelServices.config(text = "Servizi: " + get_service_list(IP))
        
        # Questa riga serve a evitare che i "late threads" scrivere a disconnessione avvenuta
        if not updating:
            labelBitrate.config(text = "")
            labelStatus.config(text = "")
            labelServices.config(text = "")
    
# Function to update the label text
def update_status(fast_mode = False):
    global updating
    while updating:
        IP = inputIP.get()
        bitrate, freq, level, snr, isi = get_status(IP)
        labelBitrate.config(text = "Bitrate:\t{}".format(bitrate) )
        if check_bitrate( bitrate ):
            labelBitrate.config(fg = "green")
        else:
            labelBitrate.config(fg = "red")

        if level != "":
            labelStatus.config(text = "Freq.:\t{} (ISI {})\nMUX rilevato:\t{}\nLivello:\t{}\nSNR:\t{}".format(freq, isi, search_mux_by_freq_and_ISI(freq, isi), level, snr) )
        
        # Questa riga serve a evitare che i "late threads" scrivere a disconnessione avvenuta
        if not updating:
            labelBitrate.config(text = "")
            labelStatus.config(text = "")
            labelServices.config(text = "")

        if not fast_mode:
            time.sleep(2)
        else:
            updating = not updating

    if fast_mode:
            updating = not updating

# Function to start or stop the updates
def toggle_update():
    global updating
    global machine
    if is_valid_ip(inputIP.get()):
        IP = inputIP.get()
        machine, version = get_machine(IP)
        labelInfoDesc.config(text = "Modello: {}\nVersione firmware: {}".format(machine, version))
        threading.Timer(1.0, update_services).start()
        if "RSR 100" in machine:
            dropdown1['values'] = mux_MF
            dropdown2['values'] = ["Profilo Unico"]
        else:
            dropdown1['values'] = mux_DVBT
            dropdown2['values'] = ["Profile 1", "Profile 2", "Profile 3"]
        updating = not updating
        if updating:
            buttonConnect.config(text = "Disconnetti")
            labelStatus.config(text = "Connessione in corso...")
            inputIP.config(state='readonly')
            inputIP.config(bg='lightgray', fg='gray')
            update_status(fast_mode=True)
            threading.Thread(target=update_status).start()
        else:
            buttonConnect.config(text = "Connetti")
            inputIP.config(state='normal')
            inputIP.config(bg='white', fg='black')
            labelBitrate.config(text = "")
            labelStatus.config(text = "")
            labelInfoDesc.config(text = "")
            labelServices.config(text = "")
    else:
        labelBitrate.config(text = "Indirizzo non valido", fg = "orange")
        labelStatus.config(text = "")

# Function to change IP address of machine
def change_IP():
    IP = inputIP.get()
    IPNew = inputIPNew.get()
    if is_valid_ip(IPNew) and is_valid_ip(IPNew):
            set_NTP(IP, gateway(IPNew))
            set_IP(IP, IPNew)
            if updating:
                toggle_update()
            label3.config(text = "Indirizzo IP cambiato. Ricollegati all'apparato.")
            labelBitrate.config(text = "")
            labelStatus.config(text = "")
            labelInfoDesc.config(text = "")
            labelServices.config(text = "")
    else:
        label3.config(text = "Indirizzo non valido")

# Function to set selected options
def set_parameters():
    IP = inputIP.get()
    if is_valid_ip(IP):
        service = dropdown1.get()
        profile = dropdown2.get()
        if profile == "":
            label2.config(text=f"Seleziona un profilo")
            return
        if search_mux_by_name(service) is not None:
            mux = search_mux_by_name(service)
        else:
            label2.config(text=f"Seleziona un servizio")
            return
        nprofile = profile.split()[1]
        set_PLS(IP)
        set_ISI(IP, mux.ISI)
        set_RX(IP, mux.ol, mux.freq, mux.pol, mux.symb, nprofile)
        label2.config(text=f"Impostato {service} su {profile}")
        labelBitrate.config(text = "...")
        labelStatus.config(text = "...")
        labelServices.config(text = "...")
        threading.Timer(15.0, update_services).start()
    else:
        labelBitrate.config(text = "Indirizzo non valido", fg = "orange")

# Create a frame for the input text field and button
frame1 = tk.Frame(root)
frame1.grid(row=0, column=0, sticky="w", pady=10)

# Create the label
label = tk.Label(frame1, text="Indirizzo IP:")
label.grid(row=0, column=0, padx=5)

# Create an input text field
inputIP = tk.Entry(frame1)
inputIP.grid(row=0, column=1, padx=5)

# Create a button next to the input text field
buttonConnect = tk.Button(frame1, text="Connetti", command=toggle_update)
buttonConnect.grid(row=0, column=2, padx=5)

# Create a button next to the input text field
buttonWeb = tk.Button(frame1, text="Pag. Web", command=webpage)
buttonWeb.grid(row=0, column=3, padx=5)

# Create a button to show version info
check_button = tk.Button(frame1, text="Info", command=show_version_info)
check_button.grid(row=0, column=4, padx=5)

# Create a label on top of the dropdown menus
labelStatusT = tk.Label(frame1, text="Stato", anchor="w", font=("Helvetica", 12, "bold"))
labelStatusT.grid(row=1, column=0, pady=5, sticky="w")

# Create a label below the input text field and button
labelBitrate = tk.Label(frame1, text=" ")
labelBitrate.grid(row=2, column=0, pady=5, columnspan=4, sticky="ew")

# Create a label below the input text field and button
labelStatus = tk.Label(frame1, text=" ")
labelStatus.grid(row=3, column=0, pady=5, columnspan=4, sticky="ew")

# Create a label below the input text field and button
labelServices = tk.Label(frame1, text=" ")
labelServices.grid(row=4, column=0, pady=5, columnspan=4, sticky="ew")

# Create a frame for the drop down menus and button
frame2 = tk.Frame(root)
frame2.grid(row=4, column=0, sticky="w", pady=10)

# Create a label on top of the dropdown menus
labelSettings = tk.Label(frame2, text="Configurazioni", anchor="w", font=("Helvetica", 12, "bold"))
labelSettings.grid(row=0, column=0, columnspan=3, pady=5, sticky="w")

# Create a label on top of the dropdown menus
labelSettingsDesc = tk.Label(frame2, text="Seleziona servizi e profili:", anchor="w")
labelSettingsDesc.grid(row=1, column=0, columnspan=3, pady=5, sticky="w")

# Create the first drop down menu
options1 = mux_list
dropdown1 = ttk.Combobox(frame2, values=options1)
dropdown1.grid(row=2, column=0, padx=5)

# Create the second drop down menu
options2 = ["Profile 1", "Profile 2", "Profile 3"]
dropdown2 = ttk.Combobox(frame2, values=options2)
dropdown2.grid(row=2, column=1, padx=5)

# Create a button next to the drop down menus
button2 = tk.Button(frame2, text="Imposta", command=set_parameters)
button2.grid(row=2, column=2, padx=5)

# Create a label below
label2 = tk.Label(frame2, text=" ")
label2.grid(row=3, column=0, columnspan=3, pady=10, sticky="w")

# Create a frame for the input text field and button
frame3 = tk.Frame(root)
frame3.grid(row=5, column=0, sticky="w", pady=10)

# Create a label on top 
labelIP = tk.Label(frame3, text="Cambio Indirizzo IP", anchor="w", font=("Helvetica", 12, "bold"))
labelIP.grid(row=0, column=0, columnspan=3, pady=5, sticky="w")

# Create the label
labelIPDesc = tk.Label(frame3, text="Indirizzo IP:")
labelIPDesc.grid(row=1, column=0, padx=5)

# Create an input text field
inputIPNew = tk.Entry(frame3)
inputIPNew.grid(row=1, column=1, padx=5)

# Create a button next to the input text field
buttonChangeIP = tk.Button(frame3, text="Imposta", command=change_IP)
buttonChangeIP.grid(row=1, column=2, padx=5)

# Create a label below
label3 = tk.Label(frame3, text=" ")
label3.grid(row=2, column=0, columnspan=3, pady=10, sticky="w")

# Create a frame for details and informations
frame4 = tk.Frame(root)
frame4.grid(row=6, column=0, sticky="w", pady=10)

# Create a label on top of details
labelInfo = tk.Label(frame4, text="Informazioni", anchor="w", font=("Helvetica", 12, "bold"))
labelInfo.grid(row=0, column=0, columnspan=3, pady=5, sticky="w")

# Create a label for details
labelInfoDesc = tk.Label(frame4, text = "", anchor="w", justify="left", width=50)
labelInfoDesc.grid(row=1, column=0, columnspan=3, pady=5, sticky="w")

# Run the application
root.mainloop()
