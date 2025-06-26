# AutoFYN URL Bot - Technical Documentation  
**Version:** 1.1.9  
**Document Version:** 1.0  
**Last Updated:** 2024  
**Authors:** Technical Team  
**Classification:** Internal Technical Documentation  

---

## Table of Contents
1. Executive Summary  
2. System Architecture  
3. Technology Stack  
4. Application Components  
5. Data Flow and Processing  
6. API Integrations  
7. Security Implementation  
8. Performance and Threading  
9. Database and Storage  
10. Configuration Management  
11. Build and Deployment  
12. Monitoring and Analytics  
13. Error Handling and Logging  
14. Code Structure  
15. Dependencies  
16. Maintenance and Troubleshooting  
17. Development Guidelines  
18. Glossary  

---

## 1. Executive Summary

### 1.1 Application Overview  
AutoFYN URL Bot is a Windows desktop application for automated web search and data extraction. It enables users to input search terms, exclude specific domains, and retrieve structured results from Google Search APIs. The application is designed for high-throughput, multi-threaded operation, and integrates with AutoFYN's authentication and analytics APIs.

### 1.2 Key Technical Achievements  
- Multi-threaded search and data extraction  
- Hardware-based device authentication  
- Real-time progress and user feedback  
- Dynamic output folder management  
- API-driven configuration and user management  
- Export to CSV/XLSX with pandas

### 1.3 Technical Specifications  
- **Frontend:** PyQt5 GUI  
- **Backend:** Python 3.x, concurrent.futures  
- **Data Output:** CSV/XLSX (pandas, openpyxl)  
- **API Integration:** Google Serper Search API, AutoFYN APIs  
- **Authentication:** Device and email-based  
- **Build System:** PyInstaller

---

## 2. System Architecture

### 2.1 High-Level Architecture  
```
┌───────────────────────────────┐
│         PyQt5 GUI             │
│  ┌─────────────────────────┐  │
│  │  User Input/Output      │  │
│  │  Progress Feedback      │  │
│  └─────────────────────────┘  │
└──────────────┬────────────────┘
              │
              ▼
┌───────────────────────────────┐
│   Processing Engine (Python)  │
│  ┌─────────────────────────┐  │
│  │  Thread Pool            │  │
│  │  Search Logic           │  │
│  │  Data Aggregation       │  │
│  └─────────────────────────┘  │
└──────────────┬────────────────┘
              │
              ▼
┌───────────────────────────────┐
│      External APIs            │
│  ┌─────────────────────────┐  │
│  │  Google Serper API      │  │
│  │  AutoFYN APIs           │  │
│  └─────────────────────────┘  │
└───────────────────────────────┘
```

### 2.2 Process Communication Flow  
1. User interacts with PyQt5 GUI  
2. GUI triggers backend processing (threaded)  
3. Backend makes API calls, processes results  
4. Results are displayed and saved  
5. Activity and status are logged via API

### 2.3 Component Responsibilities  
| Component         | Responsibility                                 |
|-------------------|------------------------------------------------|
| PyQt5 GUI         | User input, progress display, output config    |
| Processing Engine | Search, threading, data aggregation            |
| API Layer         | Authentication, analytics, config, search      |
| Storage Layer     | Output file management (CSV/XLSX)              |

---

## 3. Technology Stack

### 3.1 Core Technologies  
- **Python 3.x**: Main application language  
- **PyQt5**: GUI framework  
- **pandas, openpyxl**: Data processing and Excel export  
- **requests, urllib3**: HTTP requests  
- **concurrent.futures, threading**: Multi-threading  
- **pyinstaller**: Packaging

### 3.2 Build and Packaging  
- **PyInstaller**: Bundles Python app as a Windows executable  
- **Custom icon**: `logo.ico`

---

## 4. Application Components

### 4.1 Main Application (`RavaDynamics.py`)
- GUI logic, user input, threading, API integration, output management

### 4.2 Search Engine (`searchEngine.py`)
- Google Serper API integration, result filtering, retry logic

### 4.3 Activity Data (`activity_data.py`)
- User activity logging, app config fetch

### 4.4 Result Rearrangement (`rearrange.py`)
- Post-processing and ordering of search results

### 4.5 Resources (`res/`)
- Images, fonts, splash screens

---

## 5. Data Flow and Processing

### 5.1 Data Collection Workflow
User Input → Query Generation → API Requests → Data Processing → File Output

#### 5.1.1 Query Generation Process
1. **User Input:** The user enters a list of search terms (keywords) in the GUI.
2. **Excluded Domains:** The user can specify domains to exclude from results.
3. **Output Configuration:** The user selects the output file format (CSV or Excel) and the output folder.
4. **Query List:** Each line in the input box is treated as a separate keyword to be processed.

#### 5.1.2 API Request Pipeline (Serper API)
For each keyword, the following steps are performed:

```python
def google(ur, excluded_domains_list):
    # Initialize variables for response data
    title = ''
    kg = ''
    link1 = ''
    link2 = ''
    link3 = ''
    rating = ''  
    rating_count = ''
    phone = ''
    address = ''

    try:
        # 1. Prepare the search query payload
        payload = json.dumps({"q": ur})
        # 2. Make the /search API call
        response = session.post("https://google.serper.dev/search", headers=headers, data=payload)
        data = response.json()

        # 3. Make the /places API call
        places_payload = json.dumps({"q": ur})
        places_response = session.post("https://google.serper.dev/places", headers=headers, data=places_payload)
        places_data = places_response.json()

        # 4. Extract places data if available
        if places_data.get("places") and len(places_data["places"]) > 0:
            first_place = places_data["places"][0]
            address = first_place.get("address", "")
            rating = first_place.get("rating", "")
            rating_count = first_place.get("ratingCount", "")
            phone = first_place.get("phoneNumber", "")

        # 5. Extract Knowledge Graph data
        knowledge_graph = data.get("knowledgeGraph", {})
        if knowledge_graph:
            title = knowledge_graph.get('title', '')
            kg = knowledge_graph.get('type', '')
            link1 = knowledge_graph.get('website', None)
            # Exclude unwanted domains
            if link1 and not excludeit(link1, excluded_domains_list):
                return [ur, title, kg, link1, link2, link3, address, rating, rating_count, phone]

        # 6. Extract up to 3 organic links, filtering by excluded domains
        results = data.get("organic", [])
        count = 0
        for result in results:
            link = result.get('link', None)
            if link and not excludeit(link, excluded_domains_list):
                if count == 0:
                    title = result.get('title', None)
                    link1 = link
                elif count == 1:
                    link2 = link
                elif count == 2:
                    link3 = link
                count += 1
            if count >= 3:
                break
        return [ur, title, kg, link1, link2, link3, address, rating, rating_count, phone]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for '{ur}': {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    # In case of failure or no valid links found
    return [ur, title, kg, link1, link2, link3, address, rating, rating_count, phone]
```

##### Example Walkthrough — Keyword: "apple"
- **First API Call Output Highlights (/search):**
    - Title: Apple
    - Type: Technology company
    - Website: https://www.apple.com/
    - Organic Links:
        1. https://www.apple.com/
        2. https://www.icloud.com/
        3. https://en.wikipedia.org/wiki/Apple_Inc.
- **Second API Call Output Highlights (/places):**
    - Address: 120 W Jefferson Ave, Naperville, IL 60540
    - Rating: 3.6
    - Rating Count: 1700
    - Phone Number: (630) 536-5400
- **Final Return for "apple":**
```python
[
    "apple",
    "Apple",
    "Technology company",
    "https://www.apple.com/",
    "https://www.icloud.com/",
    "https://en.wikipedia.org/wiki/Apple_Inc.",
    "120 W Jefferson Ave, Naperville, IL 60540",
    "3.6",
    "1700",
    "(630) 536-5400"
]
```

##### Notes:
- The function loops through all keywords and performs the above process for each.
- All processed results are stored in a final list for output.

#### 5.1.3 Data Processing Pipeline
1. **Raw API Response:** JSON data from Serper API.
2. **Data Validation:** Exclude unwanted domains, ensure data completeness.
3. **Result Aggregation:** Each keyword's result is appended to a master list.
4. **Output Preparation:** The aggregated list is passed to the output function.

#### 5.1.4 Data Writing Logic (CSV / Excel Selection by User)

Before extraction, the user selects the output format (CSV or Excel) via the GUI dropdown. The program then calls the appropriate function after all keywords are processed.

##### A) write_to_csv(self, filename, result_list)
Purpose: Save processed search data into a CSV file.

```python
def write_to_csv(self, filename, result_list):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Keyword","Title","kg_type", "Link1","Link2","Link3","address","rating","ratingCount","phone"])
        writer.writerows(result_list)
```
- **Details:**
    - Overwrites file if it exists.
    - UTF-8 encoding for compatibility.
    - newline='' prevents blank lines.

##### B) write_to_excel(self, filename, result_list)
Purpose: Save processed search data into an Excel (.xlsx) file.

```python
def write_to_excel(self, filename, result_list):
    try:
        df = pd.DataFrame(result_list, columns=["Keyword","Title", "kg_type","Link","Link1","Link2","address","rating","ratingCount","phone"])
        df.to_excel(filename,index=False)
    except Exception as e:
        print(e)
        global is_file_opened
        is_file_opened = True
```
- **Details:**
    - Converts result_list to a DataFrame.
    - Handles file access errors (e.g., file open in Excel).

##### User Format Selection Logic
- The user selects the output format before starting extraction.
- The format is checked after processing, and the corresponding function is called.

#### 5.1.5 Output File Format (CSV and Excel)

The output files (both CSV and Excel) generated by the application use the following column headers, which are consistent with the data structure returned by the `google()` function in `searchEngine.py`:

**Output Columns:**
```
["Keyword", "Title", "kg_type", "Link1", "Link2", "Link3", "address", "rating", "ratingCount", "phone"]
```

- **Keyword**: The search term used.
- **Title**: The title from the Knowledge Graph or organic result.
- **kg_type**: The type/category from the Knowledge Graph.
- **Link1**: The official website or first valid organic link.
- **Link2**: The second valid organic link.
- **Link3**: The third valid organic link.
- **address**: Address from the Places API (if available).
- **rating**: Rating from the Places API (if available).
- **ratingCount**: Number of ratings from the Places API (if available).
- **phone**: Phone number from the Places API (if available).

**Example CSV/Excel Header Row:**
```
Keyword,Title,kg_type,Link1,Link2,Link3,address,rating,ratingCount,phone
```

These headers are written in the `write_to_csv` and `write_to_excel` functions:

```python
def write_to_csv(self, filename, result_list):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Keyword","Title","kg_type", "Link1","Link2","Link3","address","rating","ratingCount","phone"])
        writer.writerows(result_list)

def write_to_excel(self, filename, result_list):
    try:
        df = pd.DataFrame(result_list, columns=["Keyword","Title", "kg_type","Link","Link1","Link2","address","rating","ratingCount","phone"])
        df.to_excel(filename,index=False)
    except Exception as e:
        print(e)
        global is_file_opened
        is_file_opened = True
```

> **Note:** The same header structure is defined in the `google()` function in `searchEngine.py` and is used for both CSV and Excel outputs, ensuring consistency in exported data.

---

### 5.2 Threading and Concurrency

#### 5.2.1 Dynamic Thread Management

```python
def run_queries_in_batches(search_list, max_threads):
    users = get_active_users()
    if users == 0:
        users = 5
    max_threads = 200 // users
    threads_to_use = min(max_threads, len(search_list))
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads_to_use) as executor:
        # Submit and process tasks
        pass
```
- **Load Balancing:**
    - Total Request Limit: 200 concurrent requests
    - User-Based Distribution: max_threads = 200 / active_users
    - Minimum Guarantee: 5 threads if no other users detected
    - Dynamic Adjustment: Recalculated for each batch

---

## 6. API Integrations

### 6.1 Google Serper Search API  
- **Endpoint:** `https://google.serper.dev/search`  
- **Method:** POST  
- **Headers:** X-API-KEY, Content-Type  
- **Rate Limiting:** Managed by thread pool and user count

### 6.2 AutoFYN APIs  
- **Authentication:** `/Authentication_app/device_exist.php`  
- **Eligibility:** `/Authentication_app/is_eligible_url_bot.php`  
- **Activity Logging:** `/activities`  
- **Active User Count:** `/ActiveUsers/get_count.php`  
- **Output Path Management:** `/saved_path_api/`  
- **Version Check:** `/storage/app/public/App_CMS_images/get_latest_versioon.txt`

---

## 7. Security Implementation

### 7.1 Device Authentication

The application uses hardware-based device authentication to ensure that only authorized devices can access the AutoFYN URL Bot. This is achieved by generating a unique device identifier based on hardware properties, which is then used for user registration and eligibility checks.

#### Device ID Generation Code
```python
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
```

**Explanation:**
- The `get_device_id()` function determines the operating system and calls the appropriate platform-specific function to generate a unique device identifier.
- On **Windows**, it combines the BIOS serial, motherboard serial, and processor ID, then hashes them with SHA-256.
- On **macOS**, it combines the system serial number and hardware UUID, then hashes them.
- On **Linux**, it combines the machine-id and system UUID, then hashes them.
- The use of hardware identifiers and cryptographic hashing ensures that each installation is uniquely tied to a specific machine, providing strong device binding and tamper resistance.
- The function also detects virtual machines and handles them appropriately.

### 7.2 User Eligibility Check

Before allowing access to the application's main features, the system checks if the user (identified by email and device) is eligible to use the URL Bot. This is done via an API call to the AutoFYN authentication service.

#### Eligibility Check Code
```python
def is_eligible_url_bot():
    global mac
    global CMS_app
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
```

**Explanation:**
- The `is_eligible_url_bot()` function retrieves the user's email from the application context.
- It constructs an API URL and sends a GET request to the AutoFYN authentication endpoint.
- The API response includes an `is_eligible` flag indicating whether the user is authorized to use the URL Bot.
- If the user is not eligible, or if the API call fails, access is denied and the user is prompted to contact the administrator.

### 7.3 API Security
- API key in headers for search API  
- All API calls over HTTPS  
- User input validation and output path restrictions

### 7.4 File System Security
- Output folder restricted to user directories (Windows: Desktop, Documents, Downloads)
- Path validation to prevent system directory access

---

## 8. Performance and Threading

### 8.1 WorkerThread and Thread Pool Implementation

The core of the application's high-performance data extraction is the `WorkerThread` class, which manages concurrent API requests using a thread pool. This design ensures efficient use of system resources and enables the application to scale based on the number of active users.

#### WorkerThread Class Code
```python
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
            # Final processing after all threads have finished
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
```

### 8.2 Load Balancing and Dynamic Thread Allocation

**Load Balancing Logic:**
- The application enforces a global API request limit (e.g., 200 requests per second) to avoid overloading the backend or violating API rate limits.
- The number of threads (concurrent API requests) is dynamically calculated based on the number of active users:

```python
def get_max_threads(self):
    return max(1, api_limit_per_second // self.active_users)
```
- **Example:** If there are 4 active users, each user is allocated up to 50 threads (200 / 4).
- The thread pool size is recalculated for each batch of URLs, ensuring fair resource sharing and optimal throughput.
- If the number of active users is not available, a minimum of 1 thread is guaranteed.

**Thread Pool Execution:**
- The `run()` method of `WorkerThread` repeatedly creates a thread pool using `concurrent.futures.ThreadPoolExecutor`, submitting a batch of URLs for processing.
- Each thread independently calls the Serper API for its assigned keyword.
- Results are collected in a thread-safe manner and progress is reported to the GUI.
- After each batch, processed URLs are removed and the next batch is started until all URLs are processed or the operation is stopped.

**Benefits:**
- **Scalability:** The system can handle large numbers of keywords efficiently, scaling up or down based on user load.
- **Fairness:** All active users share the global request pool, preventing any single user from monopolizing resources.
- **Responsiveness:** The UI remains responsive, with real-time progress updates and the ability to stop the operation at any time.

---

## 9. Database and Storage

### 9.1 Storage Architecture  
- No local database; all persistent data via remote APIs
- Results saved as CSV/XLSX in user-selected folders
- Output folder path stored per user via API

---

## 10. Configuration Management

### 10.1 Remote Configuration  
- App and user settings fetched from AutoFYN APIs

### 10.2 Local Configuration  
- Version info in `version.txt`
- Dynamic QSS for UI styling

---

## 11. Build and Deployment

### 11.1 Build Process  
- Install dependencies: `pip install -r requirements.txt`
- Build executable:  
  `pyinstaller --noconsole --onefile --icon=logo.ico RavaDynamics.py`

### 11.2 Deployment  
- Distribute `.exe` to users  
- App checks for updates on startup and prompts for download

---

## 12. Monitoring and Analytics

### 12.1 Usage Tracking  
- User activity (searches, time spent) logged via API

### 12.2 System Monitoring  
- Active user count tracked via API  
- Version checks and update prompts

---

## 13. Error Handling and Logging

### 13.1 Exception Management  
- All API and file operations wrapped in try/except  
- User-friendly error dialogs via PyQt5  
- Console logging for debugging

### 13.2 User Feedback  
- Warnings and errors shown in message boxes  
- Input validation for required fields

### 13.3 API Error Handling and Status Codes

The application interacts with multiple APIs and must handle a variety of HTTP status codes and error conditions. Proper error handling ensures that users are informed of issues, and that the application can recover gracefully or provide actionable feedback.

#### Common HTTP Status Codes
| Status Code | Meaning                                 | Application Handling                        |
|-------------|-----------------------------------------|---------------------------------------------|
| 200         | Success                                 | Normal processing                          |
| 400         | Bad Request                             | User notified of invalid request           |
| 401         | Unauthorized                            | User notified, may require re-authentication|
| 403         | Forbidden                               | User notified, access denied               |
| 404         | Not Found                               | User notified, resource not found          |
| 429         | Too Many Requests (Rate Limit Exceeded) | User notified, operation paused/retried    |
| 500         | Internal Server Error                   | User notified, may retry or abort          |
| 502         | Bad Gateway                             | User notified, may retry                   |
| 503         | Service Unavailable                     | User notified, may retry                   |
| 504         | Gateway Timeout                         | User notified, may retry                   |

#### Example Error Handling Logic
```python
try:
    response = requests.get(api_url)
    if response.status_code == 200:
        # Process response
        pass
    elif response.status_code == 429:
        print("Rate limit exceeded. Please try again later.")
        # Optionally implement retry logic
    else:
        print(f"API request failed: {response.status_code}")
        # Notify user of the specific error
except requests.RequestException as e:
    print(f"Network error: {e}")
    # Notify user of connectivity issues
```

- **User Notification:** For most errors, the user is shown a message box with a clear description of the problem (e.g., rate limit, authentication failure, or server error).
- **Logging:** All errors are logged to the console for debugging and support purposes.
- **Retries:** For transient errors (e.g., 429, 502, 503), the application may implement retry logic or suggest the user try again later.

> **Note:** Proper error handling and user feedback are critical for a robust user experience, especially when dealing with external APIs and network variability.

---

## 14. Code Structure

### 14.1 Project Organization

```
AutoFYN-URL-Bot/
├── RavaDynamics.py         # Main application and GUI logic (PyQt5)
├── searchEngine.py         # Search logic, Serper API integration, result filtering
├── activity_data.py        # Activity logging, app config API
├── rearrange.py            # Result post-processing and ordering
├── requirements.txt        # Python dependencies
├── version.txt             # Version information
├── res/                    # Resources (images, fonts, splash screens)
│   ├── 1.png
│   ├── loading.gif
│   ├── Montserrat-ExtraLight.ttf
│   ├── Roboto-Light.ttf
│   ├── splash.gif
│   └── times new roman.ttf
└── logo.ico                # Application icon
```

### 14.2 Code Architecture Patterns

- **Thread Pool Pattern:**
  - Used in `WorkerThread` to manage concurrent API requests efficiently.
- **Pipeline Pattern:**
  - Data flows from user input → search → filtering → aggregation → output.
- **Modular Design:**
  - Separate modules for GUI, search logic, activity logging, and result processing.
- **Signal/Slot (Event-Driven):**
  - PyQt5 signals and slots are used for UI updates and thread communication.
- **Exception Handling:**
  - Try/except blocks for robust error handling in all network and file operations.

### 14.3 Key Algorithms

#### 14.3.1 Main Search and Threading Logic

The main search logic is managed by the `WorkerThread` class, which uses a thread pool to process keywords concurrently:

```python
def run(self):
    while self._is_running and self.urls:
        max_threads = self.get_max_threads()
        threads_to_use = min(max_threads, len(self.urls))
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads_to_use) as executor:
            futures = {executor.submit(self.scrape, url): url for url in self.urls[:threads_to_use]}
            for future in concurrent.futures.as_completed(futures):
                # Collect results, update progress
                pass
        self.urls = self.urls[threads_to_use:]
```

#### 14.3.2 Dynamic Thread Allocation

The number of threads is dynamically determined based on the number of active users, ensuring fair resource sharing:

```python
def get_max_threads(self):
    return max(1, api_limit_per_second // self.active_users)
```

- **Example:** If `api_limit_per_second = 200` and there are 4 active users, each user can use up to 50 threads.

#### 14.3.3 Result Post-Processing (Rearrangement)

After all searches are complete, results are rearranged to match the order of the input keywords:

```python
def rearrange_results(listdata, result):
    result_dict = {res[0]: res for res in result}
    last_file = [result_dict[li] for li in listdata if li in result_dict]
    return last_file
```

- This ensures the output file preserves the original keyword order.

---

## 15. Dependencies

AutoFYN URL Bot relies on several Python packages for its core functionality. All dependencies are managed via the `requirements.txt` file and can be installed using pip.

### 15.1 Required Python Packages

| Package       | Purpose                                                      |
|--------------|--------------------------------------------------------------|
| PyQt5        | GUI framework for building the desktop application           |
| pandas       | Data processing, manipulation, and CSV/Excel export          |
| requests     | HTTP requests for API communication                          |
| urllib3      | Underlying HTTP library for requests, connection pooling     |
| openpyxl     | Excel (.xlsx) file writing and manipulation                  |
| pyinstaller  | Packaging Python scripts as standalone Windows executables   |
| pillow       | Image processing (used for icons, splash screens, etc.)      |

> **Note:** Some packages (like pandas) may appear more than once in requirements.txt; only one installation is needed.

### 15.2 Installation

To install all required dependencies, run:

pip install -r requirements.txt

This will ensure your environment is set up with all necessary libraries for development and execution.

---

## 16. Maintenance and Troubleshooting

### 16.1 Common Issues and Solutions

#### 16.1.1 Authentication Problems
**Issue:** User cannot login or device not recognized

**Symptoms:**
- Login dialog appears repeatedly
- "Device not registered" errors
- Authentication timeout

**Solutions:**
```python
# Check device ID generation
deviceId = get_device_id()
print(f"Device ID: {deviceId}")

# Verify network connectivity
response = requests.get("https://autofyn.com/ActiveUsers/get_count.php")
print(f"API Status: {response.status_code}")

# Clear device cache (Windows)
# Delete registry entries or recreate device ID
```

#### 16.1.2 API Rate Limiting
**Issue:** Too many requests causing API failures

**Symptoms:**
- "Rate limit exceeded" errors
- Slow scraping performance
- Incomplete data collection

**Solutions:**
```python
# Check active user count
active_users = get_active_users()
print(f"Active users: {active_users}")

# Adjust thread count manually
max_threads = min(200 // max(active_users, 1), 50)

# Add delays between batches
import time
time.sleep(2)  # Increase delay between batches
```

#### 16.1.3 File System Issues
**Issue:** Cannot save output files

**Symptoms:**
- "Permission denied" errors
- Files not created in output directory
- Excel export failures

**Solutions:**
```python
# Check directory permissions
import os
output_dir = "path/to/output"
if not os.access(output_dir, os.W_OK):
    print("No write permission")

# Create directory if not exists
os.makedirs(output_dir, exist_ok=True)

# Validate file paths
if os.path.exists(output_path):
    print("File already exists")
```

### 16.2 Performance Optimization

#### 16.2.1 Memory Management
```python
# Monitor memory usage
import psutil
process = psutil.Process()
memory_info = process.memory_info()
print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")

# Optimize pandas operations
# Use chunking for large datasets
chunk_size = 1000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    process_chunk(chunk)
```

#### 16.2.2 Network Optimization
(See also section 16.3 for retry logic and session pooling.)

### 16.3 Diagnostic Tools

#### 16.3.1 Built-in Diagnostics
```python
def run_diagnostics():
    # Check system requirements
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()}")
    # Check dependencies
    try:
        import pandas
        print(f"Pandas version: {pandas.__version__}")
    except ImportError:
        print("Pandas not installed")
    # Check network connectivity
    try:
        response = requests.get("https://google.serper.dev", timeout=5)
        print(f"Serper API reachable: {response.status_code}")
    except:
        print("Serper API not reachable")
    # Check AutoFYN services
    try:
        response = requests.get("https://autofyn.com/ActiveUsers/get_count.php", timeout=5)
        print(f"AutoFYN API reachable: {response.status_code}")
    except:
        print("AutoFYN API not reachable")
```

#### 16.3.2 Log Analysis
```python
def analyze_logs():
    # Parse console output for errors
    error_patterns = [
        "Error processing query",
        "Failed to call API",
        "Permission denied",
        "Rate limit exceeded"
    ]
    # Count error occurrences
    with open('application.log', 'r') as log_file:
        log_content = log_file.read()
        for pattern in error_patterns:
            count = log_content.count(pattern)
            if count > 0:
                print(f"{pattern}: {count} occurrences")
    # Extract performance metrics
    import re
    duration_pattern = r'Session duration: (\d+:\d+:\d+)'
    durations = re.findall(duration_pattern, log_content)
    print(f"Average session duration: {calculate_average_duration(durations)}")
```

### 16.4 Maintenance Procedures

#### 16.4.1 Regular Maintenance Tasks
- **Daily:**
  - Monitor active user count and system performance
  - Check API rate limit usage and availability
  - Verify output file generation and integrity
  - Review error logs for recurring issues
- **Weekly:**
  - Clean up temporary files and old output directories
  - Update geographic data files if needed
  - Check for application updates
  - Review user activity analytics
- **Monthly:**
  - Analyze performance trends and optimization opportunities
  - Review and update API keys and authentication tokens
  - Backup configuration files and critical data
  - Update documentation for any changes

#### 16.4.2 Update Management
```python
def check_and_apply_updates():
    # Check for application updates
    current_version = get_current_version()
    latest_version = check_latest_version()
    if latest_version > current_version:
        print(f"Update available: {latest_version}")
        # Download update package
        update_url = get_update_url(latest_version)
        download_update(update_url)
        # Backup current version
        backup_current_installation()
        # Apply update
        apply_update_package()
        # Verify update success
        verify_update_installation()

```


## 17. Development Guidelines

To ensure code quality, maintainability, and smooth collaboration for AutoFYN URL Bot, follow these project-specific guidelines:

### 17.1 Code Standards

#### 17.1.1 Python Code Standards
- **Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code formatting.**
- Use type hints for all public functions and methods.
- Use descriptive variable and function names (e.g., `worker_thread`, `fetch_app_data`, `excluded_domains`).
- Organize code into logical modules: GUI (`RavaDynamics.py`), search/API logic (`searchEngine.py`), activity logging (`activity_data.py`), and result processing (`rearrange.py`).
- Use PyQt5 signals/slots for thread-safe UI updates.
- Handle exceptions explicitly, especially for API calls, file I/O, and threading.
- Example error handling:
```python
try:
    response = requests.get(api_url)
    response.raise_for_status()
    data = response.json()
except requests.RequestException as e:
    print(f"API error: {e}")
    QMessageBox.warning(self, "API Error", str(e))
```
- Use docstrings for all classes and public methods:
```python
def get_device_id() -> str:
    """Return a unique device identifier for authentication."""
    ...
```

### 17.2 Testing Guidelines
- Use the `unittest` framework for unit and integration tests.
- Mock API responses and file I/O in tests to avoid external dependencies.
- Test threading logic by simulating multiple concurrent API calls.
- Example:
```python
import unittest
from unittest.mock import patch

class TestSearchEngine(unittest.TestCase):
    @patch('requests.post')
    def test_google_api_success(self, mock_post):
        mock_post.return_value.json.return_value = {"knowledgeGraph": {}, "organic": []}
        result = searchEngine.google("test", [])
        self.assertIsInstance(result, list)
```
- Test GUI logic using PyQt5's QTest module for user interaction simulation (optional/advanced).

### 17.3 Version Control
- Use Git for source control.
- Branch naming: `feature/`, `bugfix/`, `hotfix/`, `release/` prefixes (e.g., `feature/thread-pool-optimization`).
- Write clear, descriptive commit messages (e.g., `fix: handle API 429 errors gracefully`).
- Use pull requests for all changes; request code review from at least one team member.
- Tag releases using semantic versioning (e.g., `v1.1.9`).

### 17.4 Release Management
- Build distributables using PyInstaller:
  ```bash
  pyinstaller --noconsole --onefile --icon=logo.ico RavaDynamics.py
  ```
- Test the built executable on a clean Windows environment before release.
- Update `version.txt` and changelog for each release.
- Announce new releases to users and provide update instructions.

### 17.5 Documentation Standards
- Keep this README up to date with all major changes.
- Document all public classes, methods, and modules with clear docstrings.
- For API integration, document endpoints, request/response formats, and error handling.
- Example docstring for a class:
```python
class WorkerThread(QThread):
    """
    Thread for running concurrent API requests and updating the GUI.
    Emits progress and status signals to the main window.
    """
    ...
```
- Add code comments for complex logic, especially in threading and API handling.

---

