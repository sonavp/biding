from django.urls import path
from .views import IndexView, ActiveListingView, CategoryView, CloseBidView, CommentView, CreateListingView, LoginView, LogoutView, RegisterView, WatchlistView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("active_listing/<int:listing_id>", ActiveListingView.as_view(), name="active_listing"),
    path("category/<str:category>", CategoryView.as_view(), name="category"),
    path("close_bid", CloseBidView.as_view(), name="close_bid"),
    path("comment", CommentView.as_view(), name="comment"),
    path("create_listing", CreateListingView.as_view(), name="create_listing"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("register", RegisterView.as_view(), name="register"),
    path("watchlist", WatchlistView.as_view(), name="watchlist"),
]
