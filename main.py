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

def get_status(IP):
    url = 'http://' + IP + '/data.json'
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'it,it-IT;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Referer': 'http://10.222.29.131/status.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'
    }

    json_data = ""
    max_retries = 10
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, verify=False)
            print(response.text)
            json_data = response.text
            break  # Exit the loop if the request is successful
        except (requests.exceptions.ConnectionError) as e:
            print(f"Connection error occurred: {e}.", end=" ")
            try:
                if len(e.args) > 0 and type(e.args[0]) is ProtocolError and isinstance(e.args[0].args[1], RemoteDisconnected):
                    print(f" Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                else:
                    break  # Exit the loop if a different error occurs
            except (IndexError, AttributeError):
                break  # Exit the loop if a different error occurs
            print()           
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            break  # Exit the loop if a different error occurs
    else:
        print("Failed to retrieve the data after multiple attempts.")

    # Parse JSON data
    if json_data != "":
        data = json.loads(json_data)

        # Extract the value
        for item in data:
            if item.get('par') == 'id177':
                bitrate = item.get('val')
            if item.get('par') == 'id3':
                freq = item.get('val')
            if item.get('par') == 'id116':
                level = item.get('val')
            if item.get('par') == 'id125':
                snr = item.get('val')

        print(bitrate)
        return bitrate, freq, level, snr
    else:
        return "Non connesso", "", "", ""

def check_bitrate(data):
    try:
        # Split the string and take the first part
        number_str = data.split()[0]
        # Convert the string to a float
        number_float = float(number_str)
        
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
            

def set_RX(IP, ol, freq, pol, symb, profile):
    # URL for the GET request
    url = "http://" + IP + "/conf_sat.html?2=" + ol + "+MHz&5=DVB-S2&9=Auto+Symbolrate&3=" + freq + "+MHz&6=" + pol + "&7=OFF&8=0+dB&4=" + symb + "+kS%2Fs&15=Loop&10=MIS&61=AUTO&270=Save+as+Profile+" + profile + "&294=REBOOT_ALL"
    print(url)
    
    max_retries = 5
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

def countdown(time_left):
    if time_left > 0:
        label3.config(text=f"Attendi {time_left:02} secondi")
        root.after(1000, countdown, time_left - 1)
    else:
        update_status()
        label3.config(text=" ")



# Create the main window
root = tk.Tk()
root.title("ROVER RB200 Configurator")
root.iconbitmap("icon.ico")

# Function to launch webpage
def webpage():
    IP = inputIP.get()
    if is_valid_ip(IP):
        webbrowser.open("http://" + IP)

# Function to update the bitrate label text
def update_status():
    IP = inputIP.get()
    if is_valid_ip(IP):
        bitrate, freq, level, snr = get_status(IP)
        labelBitrate.config(text = bitrate)
        if check_bitrate( bitrate ):
            labelBitrate.config(fg = "green")
        else:
            labelBitrate.config(fg = "red")
            
        if level != "":
            labelStatus.config(text = "Freq.:\t{}\nLivello:\t{}\nSNR:\t{}".format(freq, level, snr) )
    else:
        labelBitrate.config(text = "Indirizzo non valido", fg = "orange")
        labelStatus.config(text = " ")

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
        labelBitrate.config(text = "")
        labelStatus.config(text = "REBOOTING...")
        countdown(75)
    else:
        labelBitrate.config(text = "Indirizzo non valido", fg = "orange")

# Create a frame for the input text field and button
frame1 = tk.Frame(root)
frame1.pack(pady=10)

# Create the label
label = tk.Label(frame1, text="Indirizzo IP:")
label.pack(side=tk.LEFT)

# Create an input text field
inputIP = tk.Entry(frame1)
inputIP.pack(side=tk.LEFT, padx=5)

# Create a button next to the input text field
buttonConnect = tk.Button(frame1, text="Connetti / Aggiorna", command=update_status)
buttonConnect.pack(side=tk.LEFT, padx=5)

# Create a button next to the input text field
buttonConnect = tk.Button(frame1, text="Pag. Web", command=webpage)
buttonConnect.pack(side=tk.LEFT, padx=5)

# Create a label on top of the dropdown menus
labelStatusT = tk.Label(root, text="Stato", anchor="w", font=("Helvetica", 12, "bold"))
labelStatusT.pack(side=tk.TOP, pady=5, padx=15,  fill=tk.X)

# Create a label below the input text field and button
labelBitrate = tk.Label(root, text=" ")
labelBitrate.pack(pady=5)

# Create a label below the input text field and button
labelStatus = tk.Label(root, text=" ")
labelStatus.pack(pady=5)
        

# Create a frame for the drop down menus and button
frame2 = tk.Frame(root)
frame2.pack(pady=10)

# Create a label on top of the dropdown menus
labelSettings = tk.Label(frame2, text="Configurazioni", anchor="w", font=("Helvetica", 12, "bold"))
labelSettings.pack(side=tk.TOP, pady=5,  fill=tk.X)

# Create a label on top of the dropdown menus
labelSettingsDesc = tk.Label(frame2, text="Seleziona servizi e profili:", anchor="w")
labelSettingsDesc.pack(side=tk.TOP, pady=5,  fill=tk.X)

# Create the first drop down menu
options1 = ["MUX R", "MUX A", "MUX B"]
dropdown1 = ttk.Combobox(frame2, values=options1)
dropdown1.pack(side=tk.LEFT, padx=5)

# Create the second drop down menu
options2 = ["Profile 1", "Profile 2", "Profile 3"]
dropdown2 = ttk.Combobox(frame2, values=options2)
dropdown2.pack(side=tk.LEFT, padx=5)

# Create a button next to the drop down menus
button2 = tk.Button(frame2, text="Imposta", command=set_parameters)
button2.pack(side=tk.LEFT, padx=5)

# Create a label below
label2 = tk.Label(root, text=" ")
label2.pack(pady=10)

# Create a label below
label3 = tk.Label(root, text=" ")
label3.pack(pady=10)

# Run the application
root.mainloop()


