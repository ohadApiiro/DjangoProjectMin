from django.urls import path, include


urlpatterns = [
    path("api/mechanic/", include("crapi.mechanic.urls")),
]
