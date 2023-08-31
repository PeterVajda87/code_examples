import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import datetime as dt
import icalendar
import pytz
import uuid 
import sys

 
def sendAppointment(**kwargs):
  tz = pytz.timezone("Europe/Berlin")
  cal = icalendar.Calendar()
  cal.add('prodid', '-//My calendar application//example.com//')
  cal.add('version', '2.0')

  if 'canceled' in kwargs:
    cal.add('method', "CANCEL")
    reminderHours = 1
    startHour = 7
    start = tz.localize(dt.datetime.fromisoformat(kwargs['start_datetime']))
    event = icalendar.Event()
    event.add('attendee', kwargs['attendee'])
    event.add('organizer', 'carpool@knorr-bremse.com')
    event.add('status', 'CANCELLED')
    event.add('category', 'Event')
    event.add('summary', 'Rezervace auta')
    event.add('description', 'Tato událost byla vygenerována automaticky.')
    event.add('location', 'Vozový park')
    event.add('dtstart', start)
    event.add('dtend', tz.localize(dt.datetime.fromisoformat(kwargs['end_datetime'])))
    event.add('dtstamp', tz.localize(dt.datetime.now()))
    event['uid'] = kwargs['event_id']
    event.add('priority', 5)
    event.add('sequence', 1)
    event.add('created', tz.localize(dt.datetime.now()))
    cal.add_component(event)

  else:
    cal.add('method', "REQUEST")
    reminderHours = 1
    startHour = 7
    start = tz.localize(dt.datetime.fromisoformat(kwargs['start_datetime']))
    event = icalendar.Event()
    attendee = icalendar.vCalAddress('MAILTO:' + kwargs['attendee'])

    # attendee.params['cn'] = icalendar.vText('Max Rasmussen')
    attendee.params['ROLE'] = icalendar.vText('REQ-PARTICIPANT')
    attendee.params['RSVP'] = icalendar.vText('FALSE')


    event.add('attendee', attendee, encode=0)
    event.add('organizer', 'carpool@knorr-bremse.com')
    event.add('status', 'confirmed')
    event.add('category', 'Event')
    event.add('summary', 'Rezervace auta')
    event.add('description', 'Tato událost byla vygenerována automaticky.')
    event.add('location', 'Vozový park')
    event.add('dtstart', start)
    event.add('dtend', tz.localize(dt.datetime.fromisoformat(kwargs['end_datetime'])))
    event.add('dtstamp', tz.localize(dt.datetime.now()))
    event['uid'] = kwargs['event_id']
    event.add('priority', 5)
    event.add('sequence', 1)
    event.add('created', tz.localize(dt.datetime.now()))
    alarm = icalendar.Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add('description', "Reminder")
    alarm.add("TRIGGER;RELATED=START", "-PT{0}H".format(reminderHours))
    event.add_component(alarm)
    cal.add_component(event)
 
  msg = MIMEMultipart("alternative")

  list_of_ccs = ['recepce@knorr-bremse.com', 'jirina.berankova@knorr-bremse.com', 'katerina.topolova@knorr-bremse.com']
 
  msg["Subject"] = 'Rezervace auta'
  msg["From"] = 'automat@knorr-bremse.com'
  msg["To"] = kwargs['attendee']
  msg["Cc"] = ",".join([cc for cc in list_of_ccs if cc != kwargs['attendee']])
  msg["Content-class"] = "urn:content-classes:calendarmessage"

  html_message_text_confirm = """ \
  <html><body><p>Dobrý den,<br>úspěšně jste si rezervovali auto.<br><a href='http://10.49.34.115/carpool/create_carloan'>Zde</a> z rezervace vytvoříte přebírací protokol a můžete jezdit!</p></body></html>
  """

  html_message_text_cancel = """ \
  <html><body><p>Dobrý den,<br>zrušili jste svou rezervaci.<br><a href='http://10.49.34.115/carpool/calendar'>Zde</a> si můžete vytvořit novou!</p></body></html>
  """

  if 'canceled' in kwargs:
    html_message = MIMEText(html_message_text_cancel, "html")
  else:
    html_message = MIMEText(html_message_text_confirm, "html")

  msg.attach(html_message)
 
  filename = "invite.ics"

  if 'canceled' in kwargs:
    part = MIMEBase('text', "calendar", method="CANCEL", name=filename)
  else:
    part = MIMEBase('text', "calendar", method="REQUEST", name=filename)

  part.set_payload(cal.to_ical())
  part.add_header('Content-Description', filename)
  part.add_header("Content-class", "urn:content-classes:calendarmessage")
  part.add_header("Filename", filename)
  part.add_header("Path", filename)
  msg.attach(part)
 
  s = smtplib.SMTP('smtp-relay.corp.knorr-bremse.com')
  s.send_message(msg)
  s.quit()
