from django import template
from thingworx.models import MachinesConverter

register = template.Library()


@register.filter
def to_short_name(line):
    try:
        short_name = MachinesConverter.objects.get(machine_message_data_name=line).short_name
    except:
        short_name = MachinesConverter.objects.get(smartkpi_name=line).short_name
    return short_name


@register.simple_tag
def localize_word(word, count):

    words_dict = {}

    words_dict[0] = {
        'reakce': 'reakce',
        'sekunda': 'sekundy',
    }

    words_dict[1] = {
        'reakce': 'reakcí',
        'sekunda': 'sekund',
    }

    if 0 < count < 5:
        return words_dict[0][word]
    else:
        return words_dict[1][word]


@register.filter
def percentage(value):
    try:
        formatted_value = "{:.2%}".format(round(float(value), 4))
    except:
        formatted_value = ""
    return formatted_value

@register.filter
def get_sum(list_of_values):
    return sum(list_of_values)

@register.filter
def to_hour_range(hour):
    hours = {
        0: '00:00 - 01:00',
        1: '01:00 - 02:00',
        2: '02:00 - 03:00',
        3: '03:00 - 04:00',
        4: '04:00 - 05:00',
        5: '05:00 - 06:00',
        6: '06:00 - 07:00',
        7: '07:00 - 08:00',
        8: '08:00 - 09:00',
        9: '09:00 - 10:00',
        10: '10:00 - 11:00',
        11: '11:00 - 12:00', 
        12: '12:00 - 13:00',
        13: '13:00 - 14:00',
        14: '14:00 - 15:00',
        15: '15:00 - 16:00',
        16: '16:00 - 17:00',
        17: '17:00 - 18:00',
        18: '18:00 - 19:00',
        19: '19:00 - 20:00',
        20: '20:00 - 21:00',
        21: '21:00 - 22:00',
        22: '22:00 - 23:00',
        23: '23:00 - 00:00',
    }

    return hours[hour]
