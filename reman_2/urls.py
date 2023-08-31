from django.urls import path

from .views import index, upload_excel, root_materials, sorting, settings, disassembly, other_materials, recondition

app_name = "reman_2"

urlpatterns = [
    path("reman_2", index, name='index'),
    path("reman_2/upload_excel", upload_excel, name='upload_excel'),
    path("reman_2/root_materials", root_materials, name='root_materials'),
    path("reman_2/sorting", sorting, name='sorting'),
    path("reman_2/disassembly", disassembly, name='disassembly'),
    path("reman_2/recondition", recondition, name='recondition'),
    path("reman_2/settings", settings, name='settings'),
    path("reman_2/other_materials", other_materials, name='other_materials'),
]