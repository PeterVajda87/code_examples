from django.http import JsonResponse
from django.shortcuts import render
import datetime
import numpy as np
import json
from snowflake_connector.views import snowflake_query
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@csrf_exempt
def partno_view(request):
    data_for_selects = get_data_for_selects()
    if request.method == "POST": # uzivatel posila data na server
        request_data = json.loads(request.body)

        selected_partno = request_data.get('partno_sel') # z policka s nazvem partno_sel dostanu partnumber
        selected_machine = request_data.get('machine_sel') # stejne pro machine

        date_from = request_data.get('date_from')
        date_to = request_data.get('date_to')
        
        order_number = snowflake_query(f"SELECT ORDERNUMBER FROM SMARTKPI WHERE MACHINE = '{selected_machine}' AND PARTNUMBER = '{selected_partno}' ORDER BY CREATIONTIME DESC LIMIT 10") 
        #nutno brat sap_apo z tabulky smartkpi_orderkeyvaluedata
        
        sap_apo_query = snowflake_query(f"SELECT FLOATVALUE, TEXTVALUE FROM SMARTKPI_ORDERKEYVALUEDATA WHERE ORDERNUMBER = '{order_number[0][0]}' AND PROPERTYKEY = 'ProcessingTimeAPO-0010' LIMIT 10") #prvni hodnotu #vrati se cas a cislo

        #pokud partnumber nemá sap_apo, vrátí na frontend 0 
        try:
            #kontroluje zda je sap_apo v MIN nebo SEC
            if(sap_apo_query[0][1] == 'SEC'):
                sap_apo_seconds = int(sap_apo_query[0][0])
            else:
                sap_apo_seconds = int(sap_apo_query[0][0] * 60)
        except:
            sap_apo_seconds = 0
        dates = snowflake_query(f"WITH cte_creationtime AS (SELECT partnumber, productiontime, LAG(productiontime, 1) OVER (ORDER BY productiontime) AS previous_part, ABS(TIMESTAMPDIFF(second, productiontime, LAG(productiontime, 1) OVER (ORDER BY productiontime))) AS production_duration FROM SMARTKPI WHERE partnumber = '{selected_partno}' AND machine = '{selected_machine}' AND productiontime < '{date_to}' AND productiontime > '{date_from}') SELECT * FROM cte_creationtime WHERE production_duration IS NOT NULL AND production_duration < (5 * (SELECT MEDIAN(production_duration) FROM cte_creationtime)) ORDER BY productiontime LIMIT 10000")

        if dates: # jestli v DB existuji radky splnujici kriteria
            line_x = process_graph_arrays(dates)[0]
            line_y = process_graph_arrays(dates)[1]
            zipped = zip_arr(line_y, line_x)
            count = compute_values_graphs("count", line_y)
            mean = compute_values_graphs("mean", line_y)
            median = compute_values_graphs("median", line_y)
            ninth_percentil = compute_values_graphs("ninth_percentil", line_y)
            values_min = compute_values_graphs("values_min", line_y)
            values_max = compute_values_graphs("values_max", line_y)
            first_quartile = compute_values_graphs("first_quartile", line_y)
            third_quartile = compute_values_graphs("third_quartile", line_y)

            return JsonResponse({
                'line_x': line_x,
                'line_y': line_y,
                'values_min': int(values_min), #json neumí serializovat NUMPY datatype => nutno přetypovat na int
                'values_max': int(values_max),
                'count': count,
                'median': median,
                'mean': mean,
                'first_quartile': first_quartile,
                'third_quartile':third_quartile,
                'ninth_percentil': ninth_percentil,
                'date_from': date_from,
                'date_to': date_to,
                'data_for_selects': data_for_selects,
                'zipped': zipped,
                'selected_partno': selected_partno,
                'selected_machine': selected_machine,
                'sap_apo_seconds': sap_apo_seconds,
                'order_number': order_number,
        })
        else:
            return JsonResponse({
                "line_y" : 0,
            })

    if request.method == "GET": #uzivatel muze posilat data, ale dle vseho chce html soubor

        date_today = datetime.datetime.now()

        context = {
            'data_for_selects': data_for_selects,
            'date_today': date_today,
        }

        return render(request, 'index.html', context)

def get_data_for_selects():
    data_for_selects = {} #tady jsou data pro populovani/vyplneni select boxu na frontendu (options)
    #tuples_partnumber_machine = snowflake_query(f"SELECT DISTINCT PARTNUMBER, MACHINE FROM SMARTKPI WHERE PARTNUMBER IS NOT NULL AND NOT PARTNUMBER = ' ' AND NOT PARTNUMBER = '' AND SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com' AND CREATIONTIME > '2021-08-01' AND ORDERNUMBER LIKE '3%' ORDER BY PARTNUMBER")
    tuples_partnumber_machine = snowflake_query(f"SELECT DISTINCT PARTNUMBER, MACHINE FROM SMARTKPI WHERE PARTNUMBER IS NOT NULL AND NOT PARTNUMBER = ' ' AND NOT PARTNUMBER = '' AND SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com' AND CREATIONTIME > '2021-08-01' AND ORDERNUMBER LIKE '3_______' ORDER BY PARTNUMBER")
    for tup in tuples_partnumber_machine:
        if not tup[0] in data_for_selects:
            data_for_selects[tup[0]] = []
            data_for_selects[tup[0]].append(tup[1])
        else:
            data_for_selects[tup[0]].append(tup[1])
    return data_for_selects

def compute_values_graphs(operation, line_y):
    switcher = {
        "values_min": np.amin(line_y),
        "values_max": np.amax(line_y),
        "count": len(line_y),
        "mean": sum(line_y) / len(line_y),
        "median": np.median(line_y),
        "first_quartile": np.percentile(line_y, 25),
        "third_quartile": np.percentile(line_y, 75),
        "ninth_percentil": np.percentile(line_y, 90),
    }
    return switcher.get(operation)

def process_graph_arrays(data):
    line_x = [] # x-axis data
    line_y = [] # y-axis data
    for row in data:            
        line_y.append(row[3])
        line_x.append(str(row[1]))
    return line_x, line_y

#Google Charts vyžadují vnořený array do array
def zip_arr(arr1, arr2):
    zipped_XY = []
    zipped_XY.append(['datetime', 'rozdil casu'])
    for i in range(len(arr2)):
        zipped_XY.append([arr2[i], int(arr1[i])])
    return zipped_XY
