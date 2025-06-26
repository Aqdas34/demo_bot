import requests
import uuid

def send_activity_data(project_name,project_id, employee_id, spent_time, start, end, total_searched_keywords):
    url = f"https://autofyn.com/activities"
    params = {
        'project_name': project_name,
        'project_id':project_id,
        'employee_id': employee_id,
        'spent_time': spent_time,
        'start': start,
        'end': end,
        'total_searched_keywords': total_searched_keywords
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        # print("Data sent successfully!")
        return response.json()
    else:
        print(f"Failed to send data. Status code: {response.status_code}")
        return response.text
def fetch_app_data(project_id,mac):
    # response = requests.get('http://autofyn.com/appCms/content')
    # 04-EC-D8-4A-1D-24
    url = f"https://autofyn.com/appCms/content"
    # http://autofyn.com/appCms/content?project_id=1&mac=04-EC-D8-4A-1D-24
    # http://autofyn.com/appCms/content?project_id=1&mac=04-EC-D8-4A-1D-25
    params = {
        'project_id': project_id,
        'mac':mac
    }
    
    
    response = requests.get(url, params=params)
    # print(response.json)
    
    if response.status_code == 200:
        # print("Data sent successfully!")
        # print(response.json())
        return response.json()
    else:
        print(f"Failed to send data. Status code: {response.status_code}")
        return response.text


def get_mac_address():
    # Get the MAC address as a 48-bit positive integer
    mac_num = uuid.getnode()
    
    # Convert the integer to a hexadecimal string and format it as a MAC address
    mac_address = ':'.join(('%012x' % mac_num)[i:i+2] for i in range(0, 12, 2))
    mac_address=mac_address.upper().replace(':','-')
    return mac_address
