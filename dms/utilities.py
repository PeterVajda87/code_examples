import http.client
import json
import time


def get_translation_message(machine, substatus):
    connection = http.client.HTTPConnection("smartproductionlib.corp.knorr-bremse.com")

    headers = {"appKey": "d9e10a67-fb54-4809-9317-9fe62bd4cc7b", "Content-type": "application/json", "Accept": "application/json-compressed", "x-thingworx-session": "true"}

    body = json.dumps({ "Division": "CSV", "language": "cs-CZ", "SubStatusToken": f"{substatus}", "Machine": f"{machine}" })

    connection.request("POST", "/Thingworx/Things/KBMachineStatusDefinitionDataTable/Services/GetLocalizedList", headers=headers, body=str(body))

    resp = json.loads(connection.getresponse().read().decode())

    connection.close()

    print(resp['rows'])

    return None


def get_translation_status(level_2_status):
    connection = http.client.HTTPConnection("smartproductionlib.corp.knorr-bremse.com")

    headers = {"appKey": "d9e10a67-fb54-4809-9317-9fe62bd4cc7b", "Content-type": "application/json", "Accept": "application/json-compressed", "x-thingworx-session": "true"}

    body = json.dumps({ "language": "cs-CZ", "level2Status": f"{level_2_status}" })

    connection.request("POST", "/Thingworx/Things/KBAdministratorLevel2UtilityThing/Services/GetTokenValueForLevel2StatusLanguage?Accept=application/json-compressed&_twsr=1&Content-Type=application/json", headers=headers, body=str(body))

    resp = json.loads(connection.getresponse().read().decode())

    connection.close()

    return list(resp['rows'][0].values())[0]


def get_dlp(machine_name, start_time, end_time):
    connection = http.client.HTTPConnection("smartproductionlib.corp.knorr-bremse.com")

    headers = {"appKey": "d9e10a67-fb54-4809-9317-9fe62bd4cc7b", "Content-type": "application/json", "Accept": "application/json-compressed", "x-thingworx-session": "true"}

    body = json.dumps({"Machine": f"{machine_name}", "StartTime": start_time * 1000, "EndTime": end_time * 1000 })

    connection.request("POST", "/Thingworx/Things/KBKPILocalThingWorxDatabaseThing/Services/GetCumulativeDLP1Data", headers=headers, body=str(body))

    resp = json.loads(connection.getresponse().read().decode())

    connection.close()

    return resp['rows']



def get_downtimes(machine_name, start_time, end_time):
    connection = http.client.HTTPConnection("smartproductionlib.corp.knorr-bremse.com")

    headers = {"appKey": "d9e10a67-fb54-4809-9317-9fe62bd4cc7b", "Content-type": "application/json", "Accept": "application/json-compressed", "x-thingworx-session": "true"}

    body = json.dumps({ "language": "cs-CZ", "MachineName": f"{machine_name}", "StartTime": time.mktime(start_time.timetuple()) * 1000, "EndTime": time.mktime(end_time.timetuple()) * 1000 })

    connection.request("POST", "/Thingworx/Things/KBKPILocalThingWorxDatabaseThing/Services/GetLastMachineLocalizedStatusSelectedEntries", headers=headers, body=str(body))

    resp = json.loads(connection.getresponse().read().decode())

    connection.close()

    return resp['rows']


def get_operators_presence(machine_name, start_time, end_time):
    connection = http.client.HTTPConnection("smartproductionlib.corp.knorr-bremse.com")

    headers = {"appKey": "d9e10a67-fb54-4809-9317-9fe62bd4cc7b", "Content-type": "application/json", "Accept": "application/json-compressed", "x-thingworx-session": "true"}

    body = json.dumps({ "Machine": f"{machine_name}", "StartTime": time.mktime(start_time.timetuple()) * 1000, "EndTime": time.mktime(end_time.timetuple()) * 1000 })

    connection.request("POST", "/Thingworx/Things/KBKPILocalThingWorxDatabaseThing/Services/GetMachineAllStationStaffPerTime", headers=headers, body=str(body))

    resp = json.loads(connection.getresponse().read().decode())

    print(resp)

    connection.close()

    return resp['rows']

