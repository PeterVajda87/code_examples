from django import template
import math
import datetime

register = template.Library()

def sort_by_key_time(dict_tuple):
  time_key = datetime.datetime.strptime(dict_tuple[0], "%Y-%m-%d %H:%M")
  return time_key

@register.filter()
def multiply(number, multiplier):
  return number * float(multiplier)

@register.filter(name="position_left")
def position_left(index):
  return f'{(index % 5) * 15 + 10}vw'

@register.filter(name="position_top")
def position_top(index):
  return f'{math.floor(index / 5) * 15 + 3}vw'


@register.filter(name='range')
def filter_range(start, end):
  return range(start, end)

@register.filter(name='to_license_plate')
def to_licencse_plate(license_plate_string):
  if license_plate_string:
    license_plate = str(license_plate_string[:3]) + '-' + license_plate_string[3:]
    return license_plate

@register.filter(name='get_pictures_from_files')
def get_pictures_from_files(dictionary_items):
  new_items = [dict_item for dict_item in dictionary_items if dict_item[1][-3:] in ['png', 'jpg', 'peg']]
  return new_items


@register.filter(name='get_pdf_from_files')
def get_pdf_from_files(dictionary_items):
  new_items = [dict_item for dict_item in dictionary_items if dict_item[1][-3:] in ['pdf']]
  return new_items

@register.filter(name='get_docx_from_files')
def get_docx_from_files(dictionary_items):
  new_items = [dict_item for dict_item in dictionary_items if dict_item[1][-4:] in ['docx']]
  return new_items


@register.filter(name='pool_or_manager')
def pool_or_manager(carObject):
  if carObject.pool_car:
    return "Pool" + ' (' + str(carObject.department) + ')'
  elif carObject.manager_car:
    return str("Manažer") + ' (' + str(carObject.car_owner.first_name) + ' ' + str(carObject.car_owner.last_name) + ')'


@register.filter(name='order_by_key_time')
def order_by_key_time(list_of_dict_tuples):
  ordered_dict = {key: value for key, value in sorted(list(list_of_dict_tuples), key=sort_by_key_time, reverse=True)}
  return ordered_dict.items()


@register.filter(name='transform')
def transform(datae):
  if datae is None:
    return ''

  if isinstance(datae, datetime.datetime):
    return datae.strftime('%Y-%m-%d')

  if datae == True:
    return 'Ano'

  if datae == False:
    return 'Ne'

  if isinstance(datae, float) and datae > 20:
    return int(datae)

  return datae