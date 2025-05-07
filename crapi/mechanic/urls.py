from django.urls import include, re_path
import crapi.mechanic.views as mechanic_views

urlpatterns = [
    re_path(r"signup$", mechanic_views.SignUpView.as_view())
]
