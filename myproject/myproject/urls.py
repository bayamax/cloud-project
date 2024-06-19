from django.urls import path, include
from myapp.views import ProjectListView  # ProjectListViewのインポート
from myapp.views import SignUpView
from myapp.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('myapp/', include('myapp.urls')),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('', SignUpView.as_view(), name='signup'),  # ルートURLにProjectListViewを割り当てる
]