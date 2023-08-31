import csv
import datetime

import snowflake.connector as sc
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from django.shortcuts import render
from snowflake.connector.converter_null import SnowflakeNoConverterToPython


def test_query(request):
    snowflake_query(request.GET.get('query'))


def snowflake_query(your_query_string):
    # print(your_query_string)
    # Read private key
    with open("/home/vajdap/Knorr/snowflake_connector/rsa_key.p8", "rb") as key:
        
        # Read key
        p_key = serialization.load_pem_private_key(
            key.read(),
            password=None,
            backend=default_backend()
        )

        # Convert key to DER format
    PKB = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Define user
    USER = "peter.vajda@knorr-bremse.com"

    # Set account
    ACCOUNT = 'dz96977.west-europe.azure'

    # Establish connection
    con = sc.connect(
        user=USER,
        private_key=PKB,
        account=ACCOUNT,
        warehouse='PROD_ANALYST_WH',
        database='PROD',
        schema='M_DIGI_MANUFACTURING',
        table='SMARTKPI',
        converter_class=SnowflakeNoConverterToPython
    )

    cur = con.cursor()
    cur.execute(your_query_string)
    rows = cur.fetchall()

    cur.close()
    con.close()

    return rows
   

def obc4(request):
    # query = f""" SELECT MESSAGETYPE1, MESSAGETYPE2, MESSAGE FROM SMARTKPI_MACHINEMESSAGEDATA WHERE MACHINE LIKE '%OBC-3%' AND MESSAGETIME >= '2023-01-01'"""
    
    query = f"SELECT STATUS, SUBSTATUS, DESCRIPTION, STATUSTIME FROM SMARTKPI_MACHINESTATUSDATA WHERE MACHINE = 'KBLIBOBC04-90-ActuationAndFinishingStationThing' AND STATUSTIME >= '2023-01-10' ORDER BY STATUSTIME "
    
    context = { 'data': snowflake_query(query)}
    
    return render(request, 'snowflake_connector/obc4.html', context)
        
def lukas_vojtech():

    date_today = datetime.datetime.now()
    future_date = date_today + datetime.timedelta(days=3)
    # sloupce = machine, machine_full_name, starttime, endttime, qualifier
    # # SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com'

    data = snowflake_query(f"SELECT MACHINE, MACHINE_FULL_NAME, TO_CHAR(CONVERT_TIMEZONE('Europe/Prague',STARTTIME),'YYYY-MM-DD HH24:MI:SS'), TO_CHAR(CONVERT_TIMEZONE('Europe/Prague',ENDTIME),'YYYY-MM-DD HH24:MI:SS'), QUALIFIER FROM SHIFTCALENDAR WHERE SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com' AND STARTTIME >= '{date_today}' AND STARTTIME <= '{future_date}' ORDER BY STARTTIME DESC")
    header = ['MACHINE', 'MACHINE_FULL_NAME', 'START_TIME', 'END_TIME', 'QUALIFIER']

    with open('/home/vajdap/Knorr/media/shifts.csv', 'w') as f:
        writer = csv.writer(f,delimiter=",",lineterminator="\r\n")
        writer.writerow(header)
        writer.writerows(data)
        
    
def dms(request):
    query = f""" 
        WITH orders_materials AS (
            SELECT ORDERNUMBER, TEXTVALUE AS MATERIALNUMBER FROM SMARTKPI_ORDERKEYVALUEDATA
            WHERE CREATIONTIME >= '2023-01-25'
            AND PROPERTYKEY = 'MaterialNumber'
            AND SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com'
        ),

        orders_line AS (
            SELECT ORDERNUMBER, TEXTVALUE AS LINE FROM SMARTKPI_ORDERKEYVALUEDATA
            WHERE CREATIONTIME >= '2023-01-25'
            AND PROPERTYKEY = 'Line-0010'
            AND SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com'        
        ),

        orders_setup AS (
            SELECT ORDERNUMBER, FLOATVALUE, TEXTVALUE FROM SMARTKPI_ORDERKEYVALUEDATA
            WHERE CREATIONTIME >= '2023-01-25'
            AND PROPERTYKEY = 'SetupTimeCO-0010'
            AND SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com'
        ),

        orders_processing_time AS (
            SELECT ORDERNUMBER, FLOATVALUE, TEXTVALUE FROM SMARTKPI_ORDERKEYVALUEDATA
            WHERE CREATIONTIME >= '2023-01-25'
            AND PROPERTYKEY = 'ProcessingTimeCO-0010'
            AND SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com'
        ),
        
        orders_processing_time_other AS (
            SELECT ORDERNUMBER, FLOATVALUE, TEXTVALUE FROM SMARTKPI_ORDERKEYVALUEDATA
            WHERE CREATIONTIME >= '2023-01-25'
            AND PROPERTYKEY = 'ProcessingTime-0010'
            AND SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com'
        ),
        
        orders_processing_time_other_other AS (
            SELECT ORDERNUMBER, FLOATVALUE, TEXTVALUE FROM SMARTKPI_ORDERKEYVALUEDATA
            WHERE CREATIONTIME >= '2023-01-25'
            AND PROPERTYKEY = 'ProcessingTimeAPO-0010'
            AND SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com'
        ),

        orders_tg_max_time AS (
            SELECT ORDERNUMBER, FLOATVALUE, TEXTVALUE FROM SMARTKPI_ORDERKEYVALUEDATA
            WHERE CREATIONTIME >= '2023-01-25'
            AND PROPERTYKEY = 'tgMaxTime-0010'
            AND SOURCESYSTEM = 'smartproductionLIB.corp.knorr-bremse.com'
        )

        SELECT orders_line.LINE AS LINE, orders_materials.MATERIALNUMBER AS MATERIALNUMBER, CASE WHEN orders_setup.TEXTVALUE = 'MIN' THEN orders_setup.FLOATVALUE * 60 ELSE orders_setup.FLOATVALUE END AS SETUPTIME, CASE WHEN orders_processing_time.TEXTVALUE = 'MIN' THEN orders_processing_time.FLOATVALUE * 60 ELSE orders_processing_time.FLOATVALUE END AS PROCESSINGTIME, orders_processing_time_other.FLOATVALUE, orders_processing_time_other_other.FLOATVALUE, CASE WHEN orders_tg_max_time.TEXTVALUE = 'MIN' THEN orders_tg_max_time.FLOATVALUE * 60 ELSE orders_tg_max_time.FLOATVALUE END AS TGMAXTIME
        FROM orders_materials
        LEFT JOIN orders_setup ON orders_setup.ORDERNUMBER = orders_materials.ORDERNUMBER
        LEFT JOIN orders_processing_time ON orders_processing_time.ORDERNUMBER = orders_materials.ORDERNUMBER
        LEFT JOIN orders_processing_time_other ON orders_processing_time_other.ORDERNUMBER = orders_materials.ORDERNUMBER
        LEFT JOIN orders_processing_time_other_other ON orders_processing_time_other_other.ORDERNUMBER = orders_materials.ORDERNUMBER
        LEFT JOIN orders_tg_max_time ON orders_tg_max_time.ORDERNUMBER = orders_materials.ORDERNUMBER
        LEFT JOIN orders_line ON orders_line.ORDERNUMBER = orders_materials.ORDERNUMBER
        WHERE orders_line.LINE = 'MO5MS16C'
                """
                
    data = snowflake_query(query)
    
    print(data)