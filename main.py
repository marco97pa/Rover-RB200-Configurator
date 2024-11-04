import requests
from http.client import RemoteDisconnected
from urllib3.exceptions import ProtocolError
from requests.exceptions import ConnectionError, Timeout, ChunkedEncodingError
import webbrowser
import re
import time
import json
import tkinter as tk
from tkinter import ttk
import sys, os
from pysnmp.hlapi import *
import threading

# Initialize the flags
updating = False
machine = ""

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
                    value = str( float(value)/100 ) + " MHz"
                elif name == "Level":
                    value = str( float(value)/10 ) + " dBuV"
                elif name == "SNR":
                    value = str( float(value)/10 ) + " dB"
                elif name == "Bitrate":
                    value = str( float(value)/1000000 ) + " Mb/s"

                results[name] = value

    return results

def get_machine_name(ip_address):
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
        result = str(errorIndication)
    elif errorStatus:
        result = '%s at %s' % (errorStatus.prettyPrint(),
                                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
    else:
        for varBind in varBinds:
            value = varBind[1].prettyPrint()
            result = value

    return result
    
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
    max_retries = 10
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
    max_retries = 10
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
    max_retries = 10
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
    max_retries = 10
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
root.title("ROVER Configurator - ver. 1.3")
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

# Function to update the label text
def update_status():
    while updating:
        IP = inputIP.get()
        bitrate, freq, level, snr, isi = get_status(IP)
        
        labelBitrate.config(text = "Bitrate:\t{}".format(bitrate) )
        #labelBitrate.config(text = number_float)
        if check_bitrate( bitrate ):
            labelBitrate.config(fg = "green")
        else:
            labelBitrate.config(fg = "red")
            
        if level != "":
            labelStatus.config(text = "Freq.:\t{} (ISI {})\nLivello:\t{}\nSNR:\t{}".format(freq, isi, level, snr) )
        time.sleep(2)
    # Questa riga serve a evitare che i "late threads" scrivere a disconnessione avvenuta
    if not updating:
        labelBitrate.config(text = " ")
        labelStatus.config(text = " ")

# Function to start or stop the updates
def toggle_update():
    global updating
    global machine
    IP = inputIP.get()
    if is_valid_ip(IP):
        machine = get_machine_name(IP)
        if "RSR 100" in machine:
            dropdown1['values'] = ["Servizi MF", "MFSA", "MFPM"]
            dropdown2['values'] = ["Profilo Unico"]
        else:
            dropdown1['values'] = ["MUX R", "MUX A", "MUX B"]
            dropdown2['values'] = ["Profile 1", "Profile 2", "Profile 3"]
        updating = not updating
        if updating:
            buttonConnect.config(text = "Disconnetti")
            labelStatus.config(text = "Connessione in corso...")
            threading.Thread(target=update_status).start()
        else:
            buttonConnect.config(text = "Connetti")
            labelBitrate.config(text = " ")
            labelStatus.config(text = " ")
    else:
        labelBitrate.config(text = "Indirizzo non valido", fg = "orange")
        labelStatus.config(text = " ")

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
            labelBitrate.config(text = " ")
            labelStatus.config(text = " ")
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
        if service == "MUX R":
            ol = "10600"
            pol = "HH"
            freq = "12535.500"
            symb = "35294"
            ISI = "4"
        elif service == "MUX A":
            ol = "10600"
            pol = "VH"
            freq = "12606.000"
            symb = "35294"
            ISI = "4"
        elif service == "MUX B":
            ol = "10600"
            pol = "VH"
            freq = "12606.000"
            symb = "35294"
            ISI = "5"
        else:
            label2.config(text=f"Seleziona un servizio")
            return
        nprofile = profile.split()[1]
        set_PLS(IP)
        set_ISI(IP, ISI)
        set_RX(IP, ol, freq, pol, symb, nprofile)
    
        label2.config(text=f"Impostato {service} su {profile}")
        labelBitrate.config(text = "...")
        labelStatus.config(text = "...")
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

# Create a label on top of the dropdown menus
labelStatusT = tk.Label(root, text="Stato", anchor="w", font=("Helvetica", 12, "bold"))
labelStatusT.grid(row=1, column=0, pady=5, sticky="w")

# Create a label below the input text field and button
labelBitrate = tk.Label(root, text=" ")
labelBitrate.grid(row=2, column=0, pady=5, columnspan=4, sticky="ew")

# Create a label below the input text field and button
labelStatus = tk.Label(root, text=" ")
labelStatus.grid(row=3, column=0, pady=5, columnspan=4, sticky="ew")

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
options1 = ["MUX R", "MUX A", "MUX B"]
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

# Run the application
root.mainloop()
