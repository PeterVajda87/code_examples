from django.shortcuts import render
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.db import connections

# Create your views here.

def manometer(request):
    limits = {
        'MAX_TEMP_DIFF': 5.0001,
        'MIN_PRESSURE':  13.0,
        'MAX_PRESSURE':  15.0,
        'MIN_PRESSURE_DROP':  0.0,
        'MAX_PRESSURE_DROP':  0.30001,
    }
    
    context = {
        'limits': json.dumps(limits),
    }
    
    return render(request ,'vg/manometer.html', context)


@csrf_exempt
def get_manometer_records(request):
    MAX_TEMP_DIFF = 5.0001
    MIN_PRESSURE = 13.0
    MAX_PRESSURE = 15.0
    MIN_PRESSURE_DROP = 0.0
    MAX_PRESSURE_DROP = 0.3
    
    request_payload = json.loads(request.body)
    manometer_id = request_payload['manometer_id']
    order = request_payload['order']
    
    records = []
    
    with connections['jirkal_0003'].cursor() as cursor:
        cursor.execute(f"SELECT TOP 1 Record, Zakazka, CasTlakovani, CasOdtlakovani, DelkaTestu, TeplotaTlakovani, TeplotaOdtlakovani, TeplotniRozdil, PocatecniTlak, KonecnyTlak, TlakovyPokles, ObsluhaTlakovaniID, ObsluhaOdTlakovaniID, Rework, Vysledek, ReworkPopis, TlakPo6tiHodinach, TeplotaPo6tiHodinach, PocatecniTlakRef, TlakPo6tiHodinachRef, KonecnyTlakRef, TlakovyPoklesPo6tiHodinachRef, TlakovyPoklesRef FROM VG_Mikroporezita WHERE ManometrID='{manometer_id}' AND Zakazka='{order}' ORDER BY Record DESC")
        results = cursor.fetchall()

        for result in results:
            record = {}
            record['record'] = result[0]
            record['order'] = result[1]
            record['pressurization_time'] = result[2]
            record['depressurization_time'] = result[3]
            record['test_duration'] = result[4]
            record['pressurization_temperature'] = result[5]
            record['depressurization_temperature'] = result[6]
            record['temperature_difference'] = result[7]
            record['initial_pressure'] = result[8]
            record['final_pressure'] = result[9]
            record['pressure_drop'] = result[10]
            record['pressurization_operator'] = result[11]
            record['depressurization_operator'] = result[12]
            record['rework'] = result[13]
            record['result'] = result[14]
            record['rework_description'] = result[15]
            record['pressure_after_6_hours'] = result[16]
            record['temperature_after_6_hours'] = result[17]
            record['initial_reference_pressure'] = result[18]
            record['reference_pressure_after_6_hours'] = result[19]
            record['final_reference_pressure'] = result[20]
            record['reference_pressure_drop_after_6_hours'] = result[21]
            record['reference_pressure_drop'] = result[22]
            
            records.append(record)
            
        return JsonResponse({'records': records})
    
    
@csrf_exempt
def submit_test_beginning(request):
    MAX_TEMP_DIFF = 5.001
    MIN_PRESSURE = 13.0
    MAX_PRESSURE = 15.0
    MIN_PRESSURE_DROP = 0.0
    MAX_PRESSURE_DROP = 0.3
        
    test_data = json.loads(request.body)
    
    query = f"""
    INSERT INTO VG_Mikroporezita (Zakazka, VecneCislo, ManometrID, CasTlakovani, TeplotaTlakovani, MaxRozdilTeplot, PocatecniTlak, MinTlak, MaxTlak, MinTlakovyPokles, MaxTlakovyPokles, ObsluhaTlakovaniID, Rework, ReworkPopis, PocatecniTlakRef)
    VALUES
    ('{test_data['order']}', '{test_data['material_number']}', '{test_data['manometer_id']}', '{test_data['pressurization_time'].replace("T", " ")}', {float(test_data['pressurization_temperature'])}, {MAX_TEMP_DIFF}, {test_data['initial_pressure']}, {MIN_PRESSURE}, {MAX_PRESSURE}, {MIN_PRESSURE_DROP}, {MAX_PRESSURE_DROP}, {test_data['operator']}, {test_data['rework']}, '{test_data['rework_description']}', {round(test_data['initial_reference_pressure'], 2)})
    """
    
    with connections['jirkal_0003_rw'].cursor() as cursor:
        cursor.execute(query)

    
    return JsonResponse({'status': 'okay'})


@csrf_exempt
def submit_test_end(request):
    test_data = json.loads(request.body)
    test_duration_hours = str(test_data['test_duration'] // 60)[-2:]
    test_duration_minutes = str(int(test_data['test_duration'] % 60)).zfill(2)

    test_duration = f"{test_duration_hours}:{test_duration_minutes}"
    
    query = f"""
    UPDATE VG_Mikroporezita
    SET CasOdtlakovani = '{test_data['depressurization_time'].replace("T", " ")}',
    DelkaTestu = '{test_duration}',
    TeplotaOdtlakovani = {float(test_data['depressurization_temperature'])},
    TeplotniRozdil = {abs(float(test_data['temperature_difference']))},
    KonecnyTlak = {float(test_data['final_pressure'])},
    TlakovyPokles = {round(abs(float(test_data['pressure_drop'])), 2)},
    TlakovyPoklesRef = {round(abs(float(test_data['reference_pressure_drop'])), 2)},
    ObsluhaOdTlakovaniID = {test_data['operator']},
    Vysledek = {test_data['result']}
    WHERE record = {test_data['record']}
    """
    
    with connections['jirkal_0003_rw'].cursor() as cursor:
        cursor.execute(query)
    
    
    return JsonResponse({'status': 'okay'})


@csrf_exempt
def database_health_check(request):
    query = "SELECT 'working' FROM VG_Mikroporezita"
    
    with connections['jirkal_0003_rw'].cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchone()
        
    try:
        if result[0] == 'working':
            return JsonResponse({'result': 'online'})
    except:
        return JsonResponse({'result': 'offline'})
    