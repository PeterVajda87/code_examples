from django.shortcuts import render
from django.http import JsonResponse
import json
import csv
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from .models import Team, KPIentry
import requests
from requests.auth import HTTPBasicAuth


@csrf_exempt
def transfer_from_csv(request):
    if request.method == "GET":
        return render(request, 'valuestreamer/csv_upload.html', {})
    
    if request.method == "POST":
        try:
            kpi_definitions = get_kpi_definitions()
            request_data = json.loads(request.body)['data']
            
            for parsed_line in request_data:
                data = {}
                kpi_name = parsed_line[0]
                if kpi_name == "":
                    continue
                data['kpi_id'] = kpi_definitions[kpi_name]['kpi_id']
                data['kpi_value'] = parsed_line[1]
                
                if parsed_line[1] == "":
                    continue
                
                if int(parsed_line[1]) < 0:
                    data['kpi_value_id'] = kpi_definitions[kpi_name]['kpi_values'][0]['id']
                    data['kpi_value'] = int(parsed_line[1]) * -1
                else:
                    data['kpi_value_id'] = kpi_definitions[kpi_name]['kpi_values'][1]['id']
                    
                data['kpi_date'] = parsed_line[2]
                team_name = parsed_line[3]
            
                for team in kpi_definitions[kpi_name]['recording_teams']:
                    if team['name'] == team_name:
                        data['team_id'] = team['id']
                
                upload_kpi(data)
        except:
            return JsonResponse({'resp': 'Neco je spatne, volej Vajdu'})
            
    return JsonResponse({'resp': 'Okej'})


def upload_kpi(request_data):
    kpi_id = request_data['kpi_id']
    kpi_value_id = request_data['kpi_value_id']
    kpi_value = request_data['kpi_value']
    kpi_date = request_data['kpi_date']
    team_id = request_data['team_id']
    
    body = json.dumps({
        "values": [
            {
                "kpiValueId": f"{kpi_value_id}",
                "value": kpi_value
            },
        ]
    })
    
    r = requests.put(
        url = f"https://api-knorr-bremse.valuestreamer.de/api/exchange/kpi-data/{kpi_date}/{team_id}/{kpi_id}", 
        verify = False, 
        auth = HTTPBasicAuth('apiuser9128', 'hee5thahnohfie3theiK'),
        data = body,
        headers={'Content-Type': 'application/vs.v2.0+json'}
        )
    
    
def get_kpi_definitions():
    data = {}
    
    #### query KPIs ####
    r = requests.get(
        url = "https://api-knorr-bremse.valuestreamer.de/api/exchange/kpi",
        verify = False,
        auth = HTTPBasicAuth('apiuser9128', 'hee5thahnohfie3theiK')
    )
    
    kpis = r.json()
    for kpi in kpis:
        data[kpi['name']] = {}
        data[kpi['name']]['kpi_id'] = kpi['id']
        
    
    #### query KPI info ####
    for kpi in data:
        r = requests.get(
            url = f"https://api-knorr-bremse.valuestreamer.de/api/exchange/kpi/{data[kpi]['kpi_id']}",
            verify = False,
            auth = HTTPBasicAuth('apiuser9128', 'hee5thahnohfie3theiK')
        )
        
        json_resp = r.json()
        
        data[kpi]['is_integer'] = json_resp['kpiValueIsInteger']
        data[kpi]['time_reference'] = json_resp['kpiValueTimeReference']
    
        if 'targetValueType' in json_resp:            
            data[kpi]['target_value_type'] = json_resp['targetValueType']
            data[kpi]['target_value_scope'] = json_resp['targetValueScope']
        data[kpi]['kpi_values'] = []
        
        for kpi_value in json_resp['kpiValues']:
            kpi_value_attrs = {}
            kpi_value_attrs['id'] = kpi_value['id']
            kpi_value_attrs['name'] = kpi_value['name']
            data[kpi]['kpi_values'].append(kpi_value_attrs)
            
        data[kpi]['recording_teams'] = []
        
        for team in json_resp['recordingTeams']:
            team_attrs = {}
            team_attrs['id'] = team['id']
            team_attrs['name'] = team['name']
            data[kpi]['recording_teams'].append(team_attrs)
    
    return data
    


@csrf_exempt
def transfer(request):
    if request.method == "GET":
        data = {}
        
        #### query KPIs ####
        r = requests.get(
            url = "https://api-knorr-bremse.valuestreamer.de/api/exchange/kpi",
            verify = False,
            auth = HTTPBasicAuth('apiuser9128', 'hee5thahnohfie3theiK')
        )
        
        kpis = r.json()
        for kpi in kpis:
            data[kpi['name']] = {}
            data[kpi['name']]['kpi_id'] = kpi['id']
            
        
        #### query KPI info ####
        for kpi in data:
            r = requests.get(
                url = f"https://api-knorr-bremse.valuestreamer.de/api/exchange/kpi/{data[kpi]['kpi_id']}",
                verify = False,
                auth = HTTPBasicAuth('apiuser9128', 'hee5thahnohfie3theiK')
            )
            
            json_resp = r.json()
            
            data[kpi]['is_integer'] = json_resp['kpiValueIsInteger']
            data[kpi]['time_reference'] = json_resp['kpiValueTimeReference']
        
            if 'targetValueType' in json_resp:            
                data[kpi]['target_value_type'] = json_resp['targetValueType']
                data[kpi]['target_value_scope'] = json_resp['targetValueScope']
            data[kpi]['kpi_values'] = []
            
            for kpi_value in json_resp['kpiValues']:
                kpi_value_attrs = {}
                kpi_value_attrs['id'] = kpi_value['id']
                kpi_value_attrs['name'] = kpi_value['name']
                data[kpi]['kpi_values'].append(kpi_value_attrs)
                
            data[kpi]['recording_teams'] = []
            
            for team in json_resp['recordingTeams']:
                team_attrs = {}
                team_attrs['id'] = team['id']
                team_attrs['name'] = team['name']
                data[kpi]['recording_teams'].append(team_attrs)
        
        return render(request, 'valuestreamer/transfer.html', {'data': json.dumps(data)})
    
    
    if request.method == "POST":
        request_data = json.loads(request.body)
                
        kpi_id = request_data['kpi_id']
        kpi_value_id = request_data['kpi_value_id']
        kpi_value = request_data['kpi_value']
        kpi_date = request_data['kpi_date']
        team_id = request_data['team_id']
        
        body = json.dumps({
            "values": [
                {
                    "kpiValueId": f"{kpi_value_id}",
                    "value": kpi_value
                },
            ]
        })
        
        r = requests.put(
            url = f"https://api-knorr-bremse.valuestreamer.de/api/exchange/kpi-data/{kpi_date}/{team_id}/{kpi_id}", 
            verify = False, 
            auth = HTTPBasicAuth('apiuser9128', 'hee5thahnohfie3theiK'),
            data = body,
            headers={'Content-Type': 'application/vs.v2.0+json'}
            )
        
        print(r.json())
    
        return JsonResponse({'response': r.json()})