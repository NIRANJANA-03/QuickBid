from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create"),
    path("listing/<int:listing_id>", views.listing_page, name="listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("categories", views.categories, name="categories"),
    path('listing/<int:listing_id>/place_bid/', views.place_bid, name='place_bid'),
    path("category/<str:category_name>/", views.category_listing, name="category_listing"),
    path('listing/<int:listing_id>/add_comment/', views.add_comment, name='add_comment'),
    path('listing/<int:listing_id>/close/', views.close_listing, name='close_listing'),
    path('listing/<int:listing_id>/add_to_watchlist/', views.add_to_watchlist, name='add_to_watchlist'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path("watchlist/remove/<int:listing_id>/", views.remove_from_watchlist, name="remove_from_watchlist"),
]
