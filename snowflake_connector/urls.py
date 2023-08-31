from django.urls import URLPattern, path

from .views import snowflake_query, obc4, test_query, lukas_vojtech, dms

urlpatterns = [
    path("snowflake/index", snowflake_query),
    path("snowflake/test", test_query),
    path("snowflake/obc4", obc4),
    path("snowflake/lukas_vojtech", lukas_vojtech),
    path("snowflake/dms", dms),
]