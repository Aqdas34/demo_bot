from decimal import Decimal
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QLineEdit, QFormLayout, QFrame, QTextEdit, QComboBox, QScrollArea, QSizePolicy,QDesktopWidget,
    QDialog, QMessageBox,QFileDialog,QSpacerItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QMovie,QFontDatabase,QFont
from PyQt5.QtCore import QSize
import csv
import pandas as pd
import searchEngine
import requests
import activity_data
import concurrent
import os
import rearrange
import concurrent.futures
import datetime 
import webbrowser
import json
import platform
import subprocess
import hashlib
import time
import threading


# Loan Data Modification
is_saved_csv_file = True
is_completed = False




is_file_opened = False
excluded_domains = []
API_UPDATE_URL = "https://autofyn.com/storage/app/public/App_CMS_images/get_latest_versioon.txt"  # Replace with your API URL

is_register = False
current_version = None
latest_version = None


activate_url = "https://autofyn.com/ActiveUsers/increase_count.php"
deactivate_url = "https://autofyn.com/ActiveUsers/decrement_count.php"

current_path = ""
os_name = platform.system()
if os_name == "Windows":
    current_path = os.getcwd()
elif os_name == "Darwin":
    current_path = os.path.dirname(os.path.abspath(__file__))

def call_api(api_url):
    try:
        # Prepare the data for the POST request as JSON
       response = requests.get(api_url)
        
        # Check if the request was successful
       if response.status_code == 200:
            data = response.json()
       else:
            print(f"Failed to reach API. Status code: {response.status_code}")
    except Exception as e:
        return {'status': 'error', 'message': str(e)}




def set_path_url(email, path):
    api_url = f"https://autofyn.com/saved_path_api/set_path_url.php"
    payload = {
        'email': email,
        'path': path
    }

    # Send the POST request with the JSON payload
    try:
        response = requests.post(api_url, json=payload)

        # Check if the response is successful
        if response.status_code == 200:
            # Parse the JSON response
            json_response = response.json()
        else:
            print(f"Failed to connect. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_paths(email):
    # Construct the URL with the email parameter
    url = f"https://autofyn.com/saved_path_api/get_paths.php/{email}"
    
    try:
        # Make the GET request to the API
        response = requests.get(url)
        
        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()
        # print(data)

        # Assuming the response contains 'path' and 'email' fields
        path = data["data"]["url_saved_path"]
        # print(path)
        # email_received = data.get('email')

        return path

    except requests.exceptions.RequestException as e:
        print(f"Error making API call: {e}")
        return None

def get_device_id():
    os_name = platform.system()
    
    if os_name == "Windows":
        return get_windows_device_id()
    elif os_name == "Darwin":
        return get_mac_device_id()
    elif os_name == "Linux":
        return get_linux_device_id()
    else:
        raise Exception(f"Unsupported OS: {os_name}")

def is_virtual_machine():
    try:
        manufacturer = subprocess.check_output('wmic computersystem get manufacturer', shell=True).decode().split('\n')[1].strip()
        return "VirtualBox" in manufacturer or "VMware" in manufacturer
    except Exception:
        return False

def get_windows_device_id():
    try:
        if is_virtual_machine():
            uuid = subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()
            return uuid
        # Get BIOS serial number
        bios_serial = subprocess.check_output('wmic bios get serialnumber', shell=True).decode().split('\n')[1].strip()

        # Get motherboard serial number
        motherboard_serial = subprocess.check_output('wmic baseboard get serialnumber', shell=True).decode().split('\n')[1].strip()

        # Get processor ID
        processor_id = subprocess.check_output('wmic cpu get processorid', shell=True).decode().split('\n')[1].strip()

        # Combine these to create a unique identifier
        combined_id = bios_serial + motherboard_serial + processor_id

        # Hash the combined ID to get a unique device ID
        device_id = hashlib.sha256(combined_id.encode()).hexdigest()
        return device_id
    except Exception as e:
        raise Exception(f"Failed to retrieve device ID on Windows: {e}")


def get_mac_device_id():
    try:
        # Get system serial number
        serial_number = subprocess.check_output("system_profiler SPHardwareDataType | awk '/Serial/ {print $4}'", shell=True).decode().strip()

        # Get hardware UUID
        hardware_uuid = subprocess.check_output("system_profiler SPHardwareDataType | awk '/UUID/ {print $3}'", shell=True).decode().strip()

        # Combine these to create a unique identifier
        combined_id = serial_number + hardware_uuid

        # Hash the combined ID to get a unique device ID
        device_id = hashlib.sha256(combined_id.encode()).hexdigest()
        return device_id
    except Exception as e:
        raise Exception(f"Failed to retrieve device ID on macOS: {e}")

def get_linux_device_id():
    try:
        # Get the machine-id (unique to each installation)
        machine_id = subprocess.check_output("cat /etc/machine-id", shell=True).decode().strip()

        # Get system UUID
        system_uuid = subprocess.check_output("cat /sys/class/dmi/id/product_uuid", shell=True).decode().strip()

        # Combine these to create a unique identifier
        combined_id = machine_id + system_uuid

        # Hash the combined ID to get a unique device ID
        device_id = hashlib.sha256(combined_id.encode()).hexdigest()
        return device_id
    except Exception as e:
        raise Exception(f"Failed to retrieve device ID on Linux: {e}")

mac = get_device_id()

CMS_app = activity_data.fetch_app_data(1, mac)
user_data = CMS_app.get('user', {})
def check_for_updates():
    global current_version
    global latest_version
    current_version_path = "version.txt"

    print(current_path)
    
    if not os.path.exists(os.path.join(current_path,current_version_path)):
        return None
    
    with open(os.path.join(current_path,current_version_path), 'r') as file:
        version_data = json.load(file)
        current_version = version_data.get("version")
    
    
    
    latest_version = requests.get(API_UPDATE_URL)
    if latest_version.status_code == 200:
        
        latest_version_info = latest_version.json()
        latest_version_no = latest_version_info.get("version")
        if latest_version_no > current_version:
            return latest_version_info
    return None


#  pyinstaller --noconsole --onefile --icon=logo.ico .\RavaDynamics.py

def load_excluded_domains():
    # URL to fetch data
    url = "https://autofyn.com/excluded_domains/fetch_excluded_domains.php"
    
    try:
        # Making a GET request to fetch the JSON data
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        
        # Parsing the JSON response
        data = response.json()
        
        # Extracting domain_name from the JSON data
        domain_names = [item['domain_name'] for item in data]
        
        return domain_names
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def load_custom_font():
    # font_path = os.path.join("res", "Montserrat-ExtraLight.ttf")
    font_path = os.path.join(current_path,"res/Roboto-Light.ttf")

    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        # print("Font not loaded successfully.")
        pass
    else:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            # print(f"Loaded font: {font_families[0]}")
            return font_families[0]
    return "Roboto-Light"  # Default fallback if font loading fails

def fetch_app_data():
    response = requests.get('https://autofyn.com/appCms/1/content')
    if response.status_code == 200:

        return response.json()['data']
    else:
        raise Exception("Failed to fetch data from the website")

def check_start_time(mac):
    # Define the API endpoint
    url = "https://autofyn.com/count_users/status_time_url.php"  # Replace with the actual API URL

    # Prepare the data payload
    data = {
        'mac': mac
    }

    try:
        # Send the POST request
        response = requests.post(url, data=data)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            result = response.json()
            # print(result)
            # Check if the response contains the status and is_null fields
            if result.get('status') == 'success':
                print("success")
                return result.get('start_url_time_is_null', False)
            else:
                print(f"Error: {result.get('message')}")
                return False
        else:
            print(f"Failed to call API. Status code: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the API: {e}")
        return False

def update_url_api(mac,current_time):
    # Define the URL of the PHP script
    url = "https://autofyn.com/count_users/update_url_time.php"  # Replace with your actual URL
    
    # Prepare the data to be sent in the POST request
    data = {
        'mac': mac,
        'datetime': current_time
    }
    
    try:
        # Send the POST request
        response = requests.post(url, data=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            response_data = response.json()
            # Print the response status and message
            print(json.dumps(response_data, indent=4))
        else:
            print(f"Request failed with status code: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        # Handle any errors that occur during the request
        print(f"Error occurred: {e}")



def generate_dynamic_qss(app_data):
    background_color = app_data.get('color_background', '#f0e6e7')
    button_hover_color = app_data.get('color_button_text_hover', '#7e221b')
    footer_text_color = app_data.get('color_footer_text', '#000000')
    color_input_border = app_data.get('color_input_border', '#000000')
    color_button = app_data.get('color_button', '#000000')
    color_text = app_data.get('color_text', '#000000')
    color_button_text = app_data.get('color_button_text', '#000000')
    custom_font = load_custom_font()
    

    qss_content = f"""
    /* General */
    QWidget {{
         font-family: '{custom_font}', sans-serif;
        margin: 0;
        padding: 0;
        background-color: {background_color};
        color: {color_text};
        font-weight: 300;
    }}
    QDialog QLabel {{
        background-color: {background_color};
        color: {color_text};
    }}
    
    /* Main content */
    #logo {{
        padding-top: 10px;
    }}
    #main_content {{
        background-color: {background_color};
        padding-left: 20px;
        padding-right: 20px;
        padding-bottom: 4px;
        padding-top: 4px;
        margin-left: 10px;
        margin-right: 10px;
        border-radius: 8px;
    }}

        /*font-size: 13px;*/
    QLabel {{
    
        background-color: {background_color};
        color: {color_text};
    }}
    #loading_modal,#loading_modal_two {{
        background-color: {background_color};
        color: {color_text};
        border: 1px solid {color_button};
    }}

    QLineEdit, QTextEdit, QComboBox {{
        border: 2px solid {color_input_border};
        border-radius: 4px;
        padding: 8px;
        width: 100%;
    }}

    QLineEdit, QTextEdit, QComboBox {{
        background-color: {background_color};
    }}

    QPushButton {{
        background-color: {color_button};
        color: {color_button_text};
        padding: 5px 10px;
        border-radius: 4px;
        min-width: 100px;
        white-space: nowrap; /* Prevent text from wrapping */
    }}

    QPushButton:hover {{
        background-color: {button_hover_color};
    }}
    #output_folder_button {{
        min-width: 150px;
        white-space: nowrap; /* Prevent text from wrapping */
    }}

       /* font-size: 12px; */
    #output_format {{
        width: 90px;
        background-color: {color_button};
        color: {color_button_text};
        padding: 3px;
    }}

    /* Error Labels */
    #error {{
        color: {color_button};
    }}

    /* Footer 
        font-size: 12px;
    */
    #footer {{
        text-align: center;
        margin-top: 1px;
        color: {footer_text_color};
        padding-bottom: 4px;
    }}

    /* Scroll Area */
    #excluded_domains_box {{
        border: 2px solid {color_input_border};
        border-radius: 4px;
        min-height: 100px;
    }}
    """
    return qss_content

def get_pixmap_from_url(url):
    newurl=str(url).replace('storage/','storage/app/public/')
    response = requests.get(f'https://autofyn.com/{newurl}')
    if response.status_code == 200:
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        return pixmap
    else:
        return None    





file_name = None


api_limit_per_second = 200
class WorkerThread(QThread):
    update_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    results = []

    def __init__(self, urls, main_window):
        super().__init__()
        self.urls = urls
        self._is_running = True
        self.main_window = main_window
        self.executor = None
        self.active_users = self.get_active_users()
        if self.active_users == 0:
            self.active_users = 1

    def get_active_users(self):
        url = "https://autofyn.com/ActiveUsers/get_count.php"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('count')
                else:
                    print(f"API Error: {data.get('message')}")
            else:
                print(f"Failed to reach API. Status code: {response.status_code}")
        except Exception as e:
            print("An error occurred:", str(e))
        return 1

    def get_max_threads(self):
        return max(1, api_limit_per_second // self.active_users)

    def run(self):
        self.progress_signal.emit(0)
        self.results = []
        total_urls = len(self.urls)
        result_lock = threading.Lock()  # Lock for thread-safe access to results
        try:
            while self._is_running and self.urls:
                max_threads = self.get_max_threads()
                threads_to_use = min(max_threads, len(self.urls))

                with concurrent.futures.ThreadPoolExecutor(max_workers=threads_to_use) as executor:
                    self.executor = executor
                    futures = {executor.submit(self.scrape, url): url for url in self.urls[:threads_to_use]}

                    for future in concurrent.futures.as_completed(futures):
                        if not self._is_running:
                            break
                        try:
                            result = future.result()
                            with result_lock:  # Ensure only one thread accesses results at a time
                                self.results.append(result)
                                self.main_window.result_count += 1
                                progress = int((self.main_window.result_count / total_urls) * 100)
                                self.progress_signal.emit(progress)
                        except Exception as e:
                            print(f"Task exception: {e}")
                    # Remove the processed URLs
                    self.urls = self.urls[threads_to_use:]
                # Add a slight delay
                time.sleep(0.01)

        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            if self.executor:
                self.executor.shutdown(wait=False)
            
            # Proceed with final processing after all threads have finished
            global is_completed
            if self.main_window.download_data():
                global is_file_opened
                if not is_file_opened:
                    self.update_signal.emit("Scraping complete.")
                    is_completed = True
                    call_api(deactivate_url)
                    update_url_api(user_data.get('mac'),"null")

                else:
                    is_file_opened = False
                    is_completed = False
                    self.update_signal.emit("Close the opened file first, then hit start button to update the file again.")
                    call_api(deactivate_url)
            else:
                self.update_signal.emit("Scraping stopped.")
                is_completed = False
                call_api(deactivate_url)
            self._is_running = False


  
    def scrape(self, url):
        global excluded_domains
        if not self._is_running:
            return None
        return searchEngine.google(url, excluded_domains)

    def stop(self):
        self._is_running = False
        if self.executor:
            self.executor.shutdown(wait=False)
        self.quit()
        self.wait()


# pyinstaller --noconsole --onefile --icon=logo.ico .\RavaDynamics.py
class MainWindow(QMainWindow):
    def __init__(self,app_data):
        self.scraping_running = False
        super().__init__()
        # Set up window flags to keep the close button visible
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        font_id = QFontDatabase.addApplicationFont(os.path.join(current_path,"res/Roboto-Light.ttf"))
        font_family = None
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        default_font = QFont(font_family)  # Set default font size (e.g., 10)
        QApplication.setFont(default_font)

        self.setWindowTitle(app_data.get('text_1'))
        screen_resolution = QDesktopWidget().availableGeometry()
        window_width = int(screen_resolution.width() * 0.7)
        window_height = int(screen_resolution.height() * 0.7)
        # # Center the window on the screen
        self.setGeometry(
            (screen_resolution.width() - window_width) // 2,
            (screen_resolution.height() - window_height) // 2,
            window_width,
            window_height
        )
        # print(f"parent = {self.geometry()}")
        self.center()
        
        icon_pixmap = get_pixmap_from_url(app_data['image_1'])
        if icon_pixmap:
            scaled_icon = icon_pixmap.scaled(100, 100, Qt.KeepAspectRatio)
            self.setWindowIcon(QIcon(scaled_icon))
        if (app_data.get('text_4')):
            QTimer.singleShot(16000, lambda: self.show_notification(app_data.get('text_4')))
        

        
            
        # Changed made
        self.output_folder=''

        # global email_global


        global mac

        # mac = get_device_id()
        # CMS_app = activity_data.fetch_app_data(1, mac)
        global CMS_app
        user_data = CMS_app.get('user', {})
        email_global = user_data["email"]
        # email_global = CMS_app["user"]["email"]
        fetch_path = get_paths(email_global)
        # print(fetch_path)
        if fetch_path is not None:
            if fetch_path is not None and  os.path.exists(fetch_path):
                self.output_folder = fetch_path

        # print(f"fetch path = {fetch_path}") 
        self.user_data=''
        self.app_data=app_data

        global excluded_domains
        
        excluded_domains = load_excluded_domains()
        self.add_excluded_domains = 0
        
        

        self.worker_thread = None
        self.total_keywords = 0


        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout()
        header.setFixedHeight(160)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header.setLayout(header_layout)
        
        vertical_container = QWidget()
        vertical_layout = QVBoxLayout()


        top_spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vertical_layout.addItem(top_spacer)
        # Logo
        logo = QLabel()
        logo.setObjectName("logo")
        logo_pixmap = get_pixmap_from_url(app_data['image_2'])
        if logo_pixmap:
            # self.setWindowIcon(QIcon(icon_pixmap))
            logo.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio))
        # Add logo to header layout and center it
        logo.setAlignment(Qt.AlignCenter)
        logo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        vertical_layout.addWidget(logo)
        # Set a margin at the top of the vertical layout
        # vertical_layout.setContentsMargins(0, 25, 0, 0)  # Left, Top, Right, Bottom
        logo.setStyleSheet("padding-top: 0px;")  # Adjust the padding as needed

        search_bot_label = QLabel(" AutoFYN Search Bot")
        search_bot_label.setObjectName("search_bot_label")

        # Optionally, set a small font size for the search bot label
        search_bot_font = QFont()
        search_bot_font.setPointSize(10)  # Set to a small size like 8pt
        search_bot_font.setItalic(True)
        search_bot_font.setBold(True)
        search_bot_font.setWeight(2000)
        search_bot_label.setFont(search_bot_font)
        search_bot_label.setAlignment(Qt.AlignCenter) # added
        vertical_layout.addWidget(search_bot_label)

        bottom_spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vertical_layout.addItem(bottom_spacer)

        vertical_container.setLayout(vertical_layout)




        header_layout.addStretch(1)  # Pushes logo to the center
        header_layout.addWidget(vertical_container)
        header_layout.addStretch(1)

        
        small_font = QFont()
        small_font.setPointSize(9)  # Set to small size like 8pt
        nav = QFrame()
        nav.setObjectName("header")
        nav_bar = QHBoxLayout()
        nav.setFixedHeight(15)
        nav_bar.setContentsMargins(0, 0, 0, 0)
        nav.setLayout(nav_bar)
        version = QLabel(app_data.get('text_3'))
        version.setObjectName("version")
        version.setFont(small_font)
        # version.setFixedHeight(20)
        version.setAlignment(Qt.AlignCenter)
        nav_bar.addWidget(version)
        btn_download = QPushButton("Download")
        btn_download.setObjectName("btnDownload")
        btn_download.clicked.connect(self.download_data)
        main_layout.addWidget(header)
        main_layout.addWidget(nav)
        main_content = QFrame()
        main_content.setObjectName("main_content")
        main_content_layout = QVBoxLayout()
        main_content.setLayout(main_content_layout)
        
        form_group = QFormLayout()
        
        search_terms_label = QLabel("Search Terms:")
        self.search_terms = QTextEdit()
        self.search_terms.setLineWrapMode(QTextEdit.NoWrap)
        self.search_terms.setObjectName("search_terms")
        self.search_terms.setFixedWidth(800)
        self.search_terms.setFixedHeight(100)

        form_group.addRow(search_terms_label, self.search_terms)
  
        # Connect the resize event to the custom function
        self.resizeEvent = self.on_resize

        excluded_domains_label = QLabel("Excluded Domains:")
        # excluded_domains_label.setFont(QFont(font_family, 12))
        self.excluded_domains_box = QScrollArea()
        self.excluded_domains_box.setObjectName("excluded_domains_box")
        self.excluded_domains_box.setWidgetResizable(True)
        self.excluded_domains_widget = QWidget()
        self.excluded_domains_layout = QVBoxLayout(self.excluded_domains_widget)
        self.excluded_domains_box.setWidget(self.excluded_domains_widget)
        # self.excluded_domains_box.setFixedHeight(100)
        form_group.addRow(excluded_domains_label, self.excluded_domains_box)

        self.excluded_domains_box.setFixedWidth(1000)
        self.excluded_domains_box.setFixedHeight(100)
        
        
        
        add_domain_container = QHBoxLayout()
        self.Add_new_domain = QLabel("Add new domains :")
        self.new_domain = QLineEdit()
        self.new_domain.setObjectName("new_domain")
        self.new_domain.setPlaceholderText("Add new domain")
        add_domain_button = QPushButton("Exclude")
        add_domain_button.setObjectName("add_domain_button")
        add_domain_button.clicked.connect(self.add_domain)
        add_domain_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        add_domain_container.addWidget(self.Add_new_domain)
        add_domain_container.addWidget(self.new_domain)
        add_domain_container.addWidget(add_domain_button)
        form_group.addRow(add_domain_container)
        output_filename_label = QLabel("Output Filename:")
        self.output_filename = QLineEdit()
        self.output_filename.setObjectName("output_filename")





        form_group.addRow(output_filename_label, self.output_filename)
        self.output_filename.setFixedWidth(900)


         # **Output folder display and selection**
        output_folder_label = QLabel("Output Folder:")
        self.output_folder_display = QLineEdit(self)
        self.output_folder_display.setReadOnly(True)
        self.output_folder_display.setText(self.output_folder)
        form_group.addRow(output_folder_label, self.output_folder_display)



        main_content_layout.addLayout(form_group)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        output_folder_button = QPushButton("Select Folder")
        output_folder_button.setObjectName("output_folder_button")
        output_folder_button.clicked.connect(self.select_output_folder)
        self.output_format = QComboBox()
        self.output_format.addItems(["CSV", "XLSX"])
        self.output_format.setObjectName("output_format")
        buttons_layout.addWidget(self.output_format) 
        buttons_layout.addWidget(output_folder_button)
        
        
        
        
        # Create buttons
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.start_scraping)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.clicked.connect(self.stop_scraping)

        self.btn_close_window = QPushButton("Close Window")
        self.btn_close_window.clicked.connect(self.confirm_close)
        

        
        

        
        # Add buttons to buttons_layout
        buttons_layout.addWidget(self.btn_start)
        buttons_layout.addWidget(self.btn_stop)
        buttons_layout.addWidget(self.btn_close_window)
        
        main_content_layout.addLayout(buttons_layout)



        logo_footer_layout = QHBoxLayout()
        logo_footer = QLabel()

        logo_footer.setObjectName("logo_footer")
        logo_footer.setPixmap(QPixmap(os.path.join(current_path,'res/1.png')).scaled(200, 200, Qt.KeepAspectRatio))  # Adjust size as needed

        logo_pixmap_footer = get_pixmap_from_url(app_data['image_3'])
        if logo_pixmap_footer:
            # self.setWindowIcon(QIcon(icon_pixmap))
            logo_footer.setPixmap(logo_pixmap_footer.scaled(150, 150, Qt.KeepAspectRatio))
        


        logo_footer_layout.addWidget(logo_footer)
        logo_footer_layout.setAlignment(Qt.AlignCenter)
        
        main_content_layout.addLayout(logo_footer_layout)
        main_layout.addWidget(main_content)
        # footer = QLabel(app_data.get('text_2'))
        year = datetime.datetime.now().year

        footer = QLabel(f"&copy; {year} RAVA Dynamics | All Rights Reserved | Licensed to BowPoint")
        footer.setTextFormat(Qt.RichText)
        footer.setObjectName("footer")
        footer.setFixedHeight(40)
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
    
    def closeEvent(self, event):
        # Prevents closing the window through the OS (like Alt+F4 or close button)
        QMessageBox.information(self, "Notice", "Please use the 'Close Window' button to exit.")
        event.ignore()  # Ignore any close attempt from the OS or title bar


    

    def confirm_close(self):
        # Confirmation dialog before closing
        reply = QMessageBox.question(self, 'Exit Confirmation',
                                     "Are you sure you want to close the application?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.instance().quit()

    def on_resize(self, event):
        # Check the window's width
        if self.width() > 1200:
            # Adjust the width of the QTextEdit widget
            self.search_terms.setFixedWidth(1000)  # or any other value based on your preference
        else:
            # Set to the original width if the window is less than or equal to 1200
            self.search_terms.setFixedWidth(800)
        event.accept()
    def update_button_state(self):
        self.btn_stop.setEnabled(self.scraping_running)


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def show_notification(self, message):
        QMessageBox.warning(self, "Info", message)
    def select_output_folder(self):
        # print("select called")
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        selected_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", options=options | QFileDialog.ShowDirsOnly)
        os_name = platform.system()
        global mac
        global CMS_app
        if selected_folder:
            if os_name == "Windows":
                
                if selected_folder.startswith('C:') and not (selected_folder.endswith('Desktop') or selected_folder.endswith('Documents') or selected_folder.endswith('Downloads')):
                    QMessageBox.warning(self, "Warning", "File cannot be saved in C: drive, except in Desktop or Documents. Please select a valid folder.")
                else:
                    # Store the selected folder path in the class attribute
                    self.output_folder = selected_folder
                    # mac = get_device_id()
                    # CMS_app = activity_data.fetch_app_data(1, mac)
                    user_data = CMS_app.get('user', {})
                    email_global = user_data["email"]
                    set_path_url(email_global,self.output_folder)
                    
            else:
                # print(global_email)

                self.output_folder = selected_folder
                # mac = get_device_id()
                # global mac
                # CMS_app = activity_data.fetch_app_data(1, mac)
                user_data = CMS_app.get('user', {})
                email_global = user_data["email"]
                set_path_url(email_global,self.output_folder)
            self.output_folder_display.setText(self.output_folder)
 
    def add_domain(self):
        new_domain_text = self.new_domain.text().strip()
        if new_domain_text:
            # self.excluded_domains.insert(0,new_domain_text)
            global excluded_domains
            excluded_domains.insert(0,new_domain_text)

            self.add_excluded_domains += 1
            # print(self.excluded_domains)
            self.new_domain.clear()
            self.update_excluded_domains_box()
            # searchEngine.set_excluded_domains(self.excluded_domains)
            searchEngine.set_excluded_domains(excluded_domains)

    def update_excluded_domains_box(self):
        for i in reversed(range(self.excluded_domains_layout.count())):
            widget = self.excluded_domains_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        for doamin_index in range(self.add_excluded_domains-1,-1,-1):
            domain_item = QHBoxLayout()
            domain_item.setSpacing(0)  # Remove spacing between label  button
            domain_item.setContentsMargins(0, 0, 0, 0)  # Remove margins around the layout
            global excluded_domains
            # domain_label = QLabel(self.excluded_domains[doamin_index])
            domain_label = QLabel(excluded_domains[doamin_index])
            domain_label.setObjectName("domain_label")
            remove_button = QPushButton("Remove")
            # remove_button.setObjectName(f"remove_button_{self.excluded_domains[doamin_index]}")
            remove_button.setObjectName(f"remove_button_{excluded_domains[doamin_index]}")
            # remove_button.clicked.connect(lambda checked, domain=self.excluded_domains[doamin_index]: self.remove_domain(domain))
            remove_button.clicked.connect(lambda checked, domain=excluded_domains[doamin_index]: self.remove_domain(domain))
            remove_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            remove_button.setMaximumWidth(130)
            domain_item.addWidget(domain_label)
            domain_item.addWidget(remove_button)
            domain_container = QWidget()
            domain_container.setLayout(domain_item)
            self.excluded_domains_layout.addWidget(domain_container)

    def remove_domain(self, domain):
        global excluded_domains
        # if domain in self.excluded_domains:
        if domain in excluded_domains:
            # self.excluded_domains.remove(domain)
            excluded_domains.remove(domain)
            self.add_excluded_domains -= 1
            self.update_excluded_domains_box()

            # searchEngine.set_excluded_domains(self.excluded_domains)
            searchEngine.set_excluded_domains(excluded_domains)

    def start_scraping(self):
        

        self.scraping_running = True
        # self.update_button_state()
        if not self.user_status():
            QMessageBox.warning(self, "Danger", "Please contact the admin. You are not eligible to use this app.")
            return
        # self.initialize_directories_and_files()
        filename = self.output_filename.text().strip()
        if not filename:
            QMessageBox.warning(self, "Warning", "Please enter a valid filename.")
            return
        if not self.output_folder:
            QMessageBox.warning(self, "Warning", "Please Select the Folder.")
            return
        



        self.btn_close_window.setEnabled(False)
        self.start_time = datetime.datetime.now().replace(microsecond=0)
        # search_terms = self.read_keywords_from_file()
        search_terms = []
        ui_search_terms = self.search_terms.toPlainText().strip().split('\n')
        search_terms.extend(ui_search_terms)
        search_terms = list(filter(None, search_terms))

        if not search_terms:
            QMessageBox.warning(self, "Warning", "No keywords found in keywords.txt or search terms input.")
            return

        self.total_keywords = len(search_terms)
        self.result_count = 0
        self.estimated_time = int(self.total_keywords/50)*7 +10  # Assuming 5 seconds per keyword
        # self.timer.start(1000)  # Update time every second
        global user_data
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if check_start_time(user_data.get('mac')):
            update_url_api(user_data.get('mac'),current_time)
            call_api(activate_url)
        else:
            update_url_api(user_data.get('mac'),current_time)

        self.worker_thread = WorkerThread(search_terms, self)
        self.worker_thread.update_signal.connect(self.update_status)
        self.worker_thread.start()
        self.show_loading_modal()
        self.btn_close_window.setEnabled(True)


  

    
    def show_loading_modal_two(self):
        self.loading_modal_two = QDialog(self)
        self.loading_modal_two.setObjectName('loading_modal_two')
        self.loading_modal_two.setWindowTitle("Scraping")
        self.loading_modal_two.setFixedSize(250, 200)
        self.loading_modal_two.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowTitleHint)
        
        # # Center the loading modal
        parent_geometry = self.geometry()
        # print(parent_geometry)
        modal_geometry = self.loading_modal_two.geometry()

        center_x = (parent_geometry.center().x() - modal_geometry.width()) // 2 + 280
        center_y = (parent_geometry.center().y() - modal_geometry.height()) // 2 + 220
        self.loading_modal_two.move(center_x, center_y)

        modal_layout = QVBoxLayout()
        self.total_keywords_label = QLabel(f"Fetching Data From Database....")
        modal_layout.addWidget(self.total_keywords_label)


        loading_label = QLabel()
        loading_movie = QMovie(os.path.join(current_path,"res/loading.gif"))
        loading_movie.setScaledSize(QSize(130, 100))
        loading_label.setMovie(loading_movie)
        loading_movie.start()

        modal_layout.addWidget(loading_label, alignment=Qt.AlignCenter)
        self.loading_modal_two.setLayout(modal_layout)
        self.loading_modal_two.exec_()
    
    def update_progress_bar(self, progress):
        if hasattr(self, "progress_bar"):
            self.progress_bar.setValue(progress)

    def on_worker_complete(self, message):
        """Handle the completion of the worker thread."""
        print(message)  # Log the completion message
        self.close_loading_modal()  # Ensure the loading modal is closed
        self.worker_thread = None  # Clean up the thread reference
        global is_completed, is_saved_csv_file
        is_saved_csv_file = True
        is_completed = False

    def close_loading_modal(self):
        """Close the loading modal."""
        if hasattr(self, "loading_modal_two") and self.loading_modal_two is not None:
            self.loading_modal_two.close()
            self.loading_modal_two = None


    def user_status(self):
        try:
            global mac
            global CMS_app
            self.user_data = CMS_app.get('user', {})
            if self.user_data:
                return True
            else:
                return False
        except:return  False 


    def stop_scraping(self):
        if not self.scraping_running:
            return
        # self.update_button_state()
        if hasattr(self, 'worker_thread') and self.worker_thread is not None and self.worker_thread.isRunning():
            reply = QMessageBox.question(self, 'Stop Scraping', 'Are you sure you want to stop the scraping process?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.btn_close_window.setEnabled(True)
                call_api(deactivate_url)
                update_url_api(user_data.get('mac'),"null")
                self.worker_thread.stop()
                self.worker_thread.wait()
                # self.timer.stop()
                self.loading_modal.close()
        self.scraping_running = False

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Close Application', 'Are you sure you want to close the application?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()

        else:
            event.ignore()

    def update_status(self, message):
        QMessageBox.information(self, "Status Update", message)
        self.loading_modal.close()

    def update_scraped_data(self, count):
        self.result_count += count
        self.scraped_data_label.setText(f"Scraped data: {self.result_count}")

    def show_loading_modal(self):
        self.loading_modal = QDialog(self)
        self.loading_modal.setObjectName('loading_modal')
        self.loading_modal.setWindowTitle("Scraping")
        self.loading_modal.setFixedSize(250, 200)
        self.loading_modal.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowTitleHint)
        
        # # Center the loading modal
        parent_geometry = self.geometry()
        # print(parent_geometry)
        modal_geometry = self.loading_modal.geometry()

        center_x = (parent_geometry.center().x() - modal_geometry.width()) // 2 + 280
        center_y = (parent_geometry.center().y() - modal_geometry.height()) // 2 + 220
        self.loading_modal.move(center_x, center_y)

        modal_layout = QVBoxLayout()
        self.total_keywords_label = QLabel(f"Search Terms: {self.total_keywords}")
        modal_layout.addWidget(self.total_keywords_label)


        loading_label = QLabel()
        loading_movie = QMovie(os.path.join(current_path,"res/loading.gif"))
        loading_movie.setScaledSize(QSize(130, 100))
        loading_label.setMovie(loading_movie)
        loading_movie.start()

        modal_layout.addWidget(loading_label, alignment=Qt.AlignCenter)
        self.loading_modal.setLayout(modal_layout)
        self.loading_modal.exec_()
    def format_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"Remaining Time: {hours:02}:{minutes:02}:{seconds:02}"
    def add_seconds_to_current_time(self, seconds):
            current_time = datetime.datetime.now()
            future_time = current_time + datetime.timedelta(seconds=seconds)
            # Format the future_time as h:m:s
            formatted_future_time = future_time.strftime("%H:%M:%S")
            return formatted_future_time
    def convert_seconds_HMS(self, seconds):
            duration = datetime.timedelta(seconds=seconds)
            # Extract hours, minutes, and seconds from the duration
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            # Format as h:m:s
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"
            return formatted_time
    def convert_Time_HMS(self, start_time):
            # future_time =  datetime.timedelta(seconds=seconds)
            # Format the future_time as h:m:s
            formatted_future_time = start_time.strftime("%H:%M:%S")
            return formatted_future_time
    def update_time(self):
        self.estimated_time -= 1
        self.time_remaining_label.setText(self.format_time(self.estimated_time))
        if self.estimated_time <= 0:
            self.timer.stop()
    # Function to calculate time spent
    def calculate_time_spent(self, start_time, end_time):   
        # Calculate time difference in seconds
        time_difference = (end_time - start_time)
        
       # Extract hours, minutes, and seconds from the time difference
        hours, remainder = divmod(time_difference.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format the time difference as h:m:s
        formatted_time_difference = f"{int(hours)}:{int(minutes)}:{int(seconds)}"
        
        return formatted_time_difference

    def download_data(self):
        # print("download")
        filename = self.output_filename.text().strip()
        global file_name
        file_name = filename
        file_type = self.output_format.currentText()
        # result_list = searchEngine.get_result_list()
        result_list=self.worker_thread.results
        current_time=datetime.datetime.now().replace(microsecond=0)
        strtime=self.start_time
        appname=self.app_data.get('name')
        user_id=self.user_data.get('id')
        tkeywords=self.total_keywords

        spent_time=self.calculate_time_spent(strtime,current_time)
        activity_data.send_activity_data(appname,4, user_id, spent_time, strtime, current_time,tkeywords)
   
        if not self.output_folder:
            self.output_folder='outputs'
            
            
        # print(result_list)
        if any(res is None for res in result_list):
            # print("if")
            return False
        
        
        search_terms = []
        ui_search_terms = self.search_terms.toPlainText().strip().split('\n')
        search_terms.extend(ui_search_terms)
        search_terms = list(filter(None, search_terms))
        # last_file = rearrange.rearrange_results(self.worker_thread.urls, result_list)
        last_file = rearrange.rearrange_results(search_terms, result_list)
        # last_file = result_list
        # print(last_file)
        global is_saved_csv_file
        if file_type == "CSV":
                is_saved_csv_file = True
                file_name = f"{self.output_folder}/{filename}.csv"
                try:
                    self.write_to_csv(file_name, last_file)
                except Exception as e:
                    # print(e)
                    global is_file_opened
                    is_file_opened = True

        elif file_type == "XLSX":
            is_saved_csv_file = False
            file_name = f"{self.output_folder}/{filename}.xlsx"
            # print(f"filename = {file_name}")
            self.write_to_excel(file_name, last_file)
        searchEngine.resultList.clear()
        self.result_list=''  
        last_file=''  
        return True       
    def write_to_csv(self, filename, result_list):
    
        # Attempt to open the file for writing

        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Keyword","Title",'kg_type', "Link1","Link2","Link3","address","rating","ratingCount","phone"])
            # print(f"list = {result_list}")
            writer.writerows(result_list)
        

    def write_to_excel(self, filename, result_list):
        try:
            df = pd.DataFrame(result_list, columns=["Keyword","Title", "kg_type","Link","Link1","Link2","address","rating","ratingCount","phone"])
            df.to_excel(filename,index=False)
        except Exception as e :
            print(e)
            global is_file_opened
            is_file_opened = True
    def refresh_app(self):
        global excluded_domains
    # Clear excluded domains array
        # self.excluded_domains.clear()
        excluded_domains.clear()

        # Re-import excluded domains from excluded.txt
        with open('inputs/excluded.txt', 'r') as excluded_file:
            # self.excluded_domains.extend(line.strip() for line in excluded_file if line.strip())
            excluded_domains.extend(line.strip() for line in excluded_file if line.strip())

        # Clear search term keywords array (urls)
        self.worker_thread.urls.clear()

        searchEngine.resultList.clear()
        self.result_list=''





def show_splash_screen(app, app_data):
    background_color = app_data.get('color_background', '#f0e6e7')
    splash = QWidget()
    splash.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    
    # Get screen resolution
    screen_resolution = QDesktopWidget().availableGeometry()
    screen_width = screen_resolution.width()
    screen_height = screen_resolution.height()
    
    # Calculate window size (60% of screen size)
    window_width = int(screen_width * 0.6)
    window_height = int(screen_height * 0.6)
    
    # Center the window on the screen
    splash.setGeometry(
        (screen_width - window_width) // 2,
        (screen_height - window_height) // 2,
        window_width,
        window_height
    )
    
    splash.setStyleSheet(f"background-color: {background_color}")  # Set background color
    
    layout = QVBoxLayout(splash)
    layout.setAlignment(Qt.AlignCenter)  # Center the layout
    
    splash_image = QLabel()
    
    # Load the pixmap to get the original size
    pixmap = QPixmap(os.path.join(current_path,"res/splash.gif"))
    if pixmap.isNull():
        # Handle the case where the image couldn't be loaded
        print("Error: Unable to load splash.gif")
        return splash
    
    original_width = pixmap.width()
    original_height = pixmap.height()
    
    if original_height == 0:
        # Prevent division by zero by setting a default aspect ratio
        aspect_ratio = 1.0  # Default to square if height is zero
    else:
        aspect_ratio = original_width / original_height
    
    # Calculate scaled size to maintain aspect ratio
    window_aspect_ratio = window_width / window_height
    if window_aspect_ratio > aspect_ratio:
        # Window is wider than the image aspect ratio
        scaled_height = window_height
        scaled_width = int(window_height * aspect_ratio)
    else:
        # Window is taller than the image aspect ratio
        scaled_width = window_width
        scaled_height = int(window_width / aspect_ratio)
    
    # Ensure scaled dimensions are at least 1 pixel
    scaled_width = max(1, scaled_width)
    scaled_height = max(1, scaled_height)
    
    # Initialize QMovie after obtaining the size
    splash_movie = QMovie(os.path.join(current_path,"res/splash.gif"))
    if not splash_movie.isValid():
        # Handle invalid movie
        print("Error: Unable to load splash.gif as a QMovie")
        return splash
    
    splash_movie.setScaledSize(QSize(scaled_width, scaled_height))
    splash_movie.start()
    
    splash_image.setMovie(splash_movie)
    splash_image.setAlignment(Qt.AlignCenter)
    layout.addWidget(splash_image)
    
    splash.setLayout(layout)
    splash.show()
    
    return splash
def run_application():
    project_id=1
    # mac=activity_data.get_mac_address()    
    global mac
    global CMS_app
    CMS_app=activity_data.fetch_app_data(project_id,mac)
    app_data = CMS_app.get('data', {})
    
    
    app = QApplication(sys.argv)
    app.setStyleSheet(generate_dynamic_qss(app_data))
    splash = show_splash_screen(app,app_data)
 
    # print(app_data)
    main_window = MainWindow(app_data)
    QTimer.singleShot(5000, splash.close)
    QTimer.singleShot(5000, lambda: main_window.showNormal())
    
    # window.showMaximized()
    sys.exit(app.exec_())





class RegisterWindow(QMainWindow):
    def __init__(self, app_data):
        super().__init__()
        self.app_data = app_data
        self.setWindowTitle("Register")
        self.setFixedSize(400, 300)

        # Center the window on the screen
        screen_resolution = QDesktopWidget().availableGeometry()
        self.setGeometry(
            (screen_resolution.width() - 400) // 2,
            (screen_resolution.height() - 300) // 2,
            400,
            300
        )

        main_layout = QVBoxLayout()

        # Form layout for registration fields
        form_layout = QFormLayout()

        # Email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        form_layout.addRow(QLabel("Email:"), self.email_input)

        # Add form layout to main layout
        main_layout.addLayout(form_layout)

        # Notification label (initially hidden)
        self.notification = QLabel("")
        self.notification.setAlignment(Qt.AlignCenter)
        self.notification.setStyleSheet("color: red;")
        self.notification.setFixedHeight(40)
        self.notification.hide()  # Hidden until a notification is shown
        main_layout.addWidget(self.notification)

        # Register and cancel buttons
        register_button = QPushButton("Register")
        register_button.clicked.connect(self.register_user)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(register_button)
        button_layout.addWidget(cancel_button)

        # Add buttons to the main layout
        main_layout.addLayout(button_layout)

        # Set main widget and layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Apply custom styles (QSS)
        self.setStyleSheet(generate_dynamic_qss(app_data))

    def register_user(self):
        email = self.email_input.text().strip()

        if not email:
            self.show_notification("Please enter an email address.")
            return
        global is_register
        # device_id = get_device_id()
        global mac
        device_id = mac
        # Construct the API URL
        api_url = f"https://autofyn.com/Authentication_app/device_exist.php/{email}/{device_id}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                response_data = response.json()  # Get the JSON response
                status = response_data.get("status", "Unknown status")
                message = response_data.get("message", "No message provided")  # Assuming the API returns a message
                is_register = (status == "success")
                
                # Show the status and message from the response
                self.show_notification(f"Registration status: {status}\nMessage: {message}", success=is_register)
            else:
                self.show_notification("Failed to reach the server.")
        except requests.RequestException as e:
            self.show_notification(f"Error: {str(e)}")

    def show_notification(self, message, success=False):
        # Display a message to the user
        self.notification.setText(message)
        self.notification.setStyleSheet("color: green;" if success else "color: red;")
        self.notification.show()
    
def is_eligible_url_bot():
    # mac = get_device_id()
    global mac
    global CMS_app
    # CMS_app = activity_data.fetch_app_data(1, mac)
    user_data = CMS_app.get('user', {})
    print(user_data)
    
    email = user_data.get('email')

    if not email:
        raise ValueError("Email not found in user data.")

    # Construct the API URL
    api_url = f"https://autofyn.com/Authentication_app/is_eligible_url_bot.php/{email}"
    
    try:
        # Make a GET request to the API
        response = requests.get(api_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()  # Parse the JSON response
            
            # Extract the 'is_eligible' value from the response
            is_eligible = response_data.get('is_eligible', False)
            
            # Return True if eligible, False otherwise
            return is_eligible
        else:
            # Handle failed responses
            print(f"Failed to reach the server. Status code: {response.status_code}")
            return False
    
    except requests.RequestException as e:
        # Handle any exceptions during the request
        print(f"Error occurred: {str(e)}")
        return False


if __name__ == "__main__":
    app = QApplication([])
    # app_data = CMS_app.get('data', {})
    # print(app_data.get('text_2'))

    # mac = get_device_id()
    # print(mac)
    # CMS_app = activity_data.fetch_app_data(1, mac)
    # print(CMS_app)
    # user_data = CMS_app.get('user', {})
  

    # print(current_path)
    
    latest_version = CMS_app["data"]["text_3"]
    import re
    match = re.search(r"v(\d+\.\d+\.\d+)", latest_version)
    if match:
        latest_version = match.group(1)
    is_update = False
    if not user_data:
        app_data = {
            'text_2': 'Footer Text',
            'color_background': '#f0e6e7',
            'color_text': '#000000',
            'color_button_text_hover': '#7e221b',
            'color_input_border': '#000000',
            'color_button': '#000000',
            'color_button_text': '#FFFFFF'
        }
        register = RegisterWindow(app_data)
        register.show()
        result = app.exec_()

        if is_register:
            current_version = None
        try:
            with open(os.path.join(current_path,"version.txt","r")) as file:
                version_data = json.load(file)
                current_version = version_data.get("version")
            # print(f"current version {current_version}")
            # print(f"latest version {latest_version}")
        except:
            # if latest_version_info:
            if latest_version != current_version:
                download_url = "https://autofyn.com/download_exe/index.php"
                reply = QMessageBox.question(app.activeWindow(), "Update Available", "A new version is available. Do you want to update now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
                if reply == QMessageBox.Yes:
                    is_update = True
                    webbrowser.open(download_url)
                    QMessageBox.warning(app.activeWindow(), "Danger", "Please Download the latest version before using it.")
                    app.quit()
            
            if not is_update:
                # initialize_directories_and_files()
                if is_eligible_url_bot():
                    run_application()
                else:
                    QMessageBox.warning(None, "Danger", "Please contact the admin. You are not allowed to use the Url Bot.")
                app.quit()
    else:


        current_version = None
        try:
            with open(os.path.join(current_path,"version.txt"), 'r') as file:
                version_data = json.load(file)
                current_version = version_data.get("version")
            # print(f"current version {current_version}")
            # print(f"latest version {latest_version}")
        except:
            pass
        if latest_version != current_version:
            download_url = "https://autofyn.com/download_exe/index.php"
            reply = QMessageBox.question(app.activeWindow(), "Update Available", "A new version is available. Do you want to update now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
            if reply == QMessageBox.Yes:
                is_update =  True
                webbrowser.open(download_url)
                QMessageBox.warning(app.activeWindow(), "Danger", "Please Download the latest version before using it.")
                app.quit()
        if not is_update:
            if is_eligible_url_bot():
                run_application()
            else:
                QMessageBox.warning(app.activeWindow(), "Danger", "Please contact the admin. You are not allowed to use the Url Bot.")
            app.quit()



         