from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from auctions.models import User
from .models import *
from django.contrib import messages 
def index(request):
    listings = AuctionListing.objects.filter(active=True)
    return render(request, "auctions/index.html", {'listings': listings})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import AuctionListing, Bid, Comment, Watchlist
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden

@login_required
def create_listing(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        starting_bid = request.POST.get("starting_bid")
        image_url = request.POST.get("image_url")
        category = request.POST.get("category")

        listing = AuctionListing(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_url=image_url,
            category=category,
            creator=request.user,
        )
        listing.save()
        return redirect("listing", listing.id)
    return render(request, "auctions/create.html")

def active_listings(request):
    listings = AuctionListing.objects.filter(active=True)
    return render(request, "auctions/index.html", {"listings": listings})

def listing_page(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    comments = listing.comments.all()
    user_watchlist = None

    if request.user.is_authenticated:
        user_watchlist = Watchlist.objects.filter(user=request.user, listing=listing).exists()

    if request.method == "POST" and listing.active:
        if "bid" in request.POST:
            bid_amount = request.POST.get("bid_amount")
            if float(bid_amount) > listing.starting_bid:
                Bid.objects.create(listing=listing, bidder=request.user, amount=bid_amount)
        elif "close" in request.POST and request.user == listing.creator:
            listing.active = False
            listing.save()
        elif "comment" in request.POST:
            content = request.POST.get("comment")
            Comment.objects.create(listing=listing, user=request.user, content=content)
    return render(
        request,
        "auctions/listing.html",
        {"listing": listing, "comments": comments, "user_watchlist": user_watchlist},
    )

@login_required
def watchlist(request):
    watchlist = Watchlist.objects.filter(user=request.user)
    return render(request, 'auctions/watchlist.html', {
        'watchlist': watchlist
    })

@login_required
def listing_detail(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    is_in_watchlist = Watchlist.objects.filter(user=request.user, listing=listing).exists()
    return render(request, 'auctions/listing.html', {
        'listing': listing,
        'is_in_watchlist': is_in_watchlist,  
    })

 
def categories(request):
    unique_categories = AuctionListing.objects.values_list("category", flat=True).distinct()
    return render(request, "auctions/categories.html", {"categories": unique_categories})

def category_listing(request, category_name):
    listings = AuctionListing.objects.filter(category=category_name)
    return render(request, "auctions/category_listing.html", {
        "category_name": category_name,
        "listings": listings
    })

@login_required
def place_bid(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    highest_bid = None
    if request.method == 'POST':
        bid_amount = request.POST.get('bid')
        
        try:
            bid_amount = float(bid_amount)
        except ValueError:
            messages.error(request, "Invalid bid amount.")
            return redirect('place_bid', listing_id=listing.id)
        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()

        print(f"Highest Bid: {highest_bid.amount if highest_bid else 'None'}")
        print(f"User's Bid: {bid_amount}")
        if highest_bid and bid_amount <= highest_bid.amount:
            messages.error(request, "Your bid must be higher than the current highest bid.")
            return redirect('place_bid', listing_id=listing.id)

        Bid.objects.create(
            listing=listing,
            bidder=request.user,
            amount=bid_amount
        )
        messages.success(request, "Your bid has been placed successfully!")
        return redirect('listing', listing_id=listing.id)
    
    else:
        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()

    return render(request, 'auctions/place_bid.html', {
        'listing': listing,
        'highest_bid': highest_bid,
    })



@login_required
def add_comment(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)

    if request.method == 'POST':
        content = request.POST.get('comment')
        if content:
            comment = Comment.objects.create(
                listing=listing,
                user=request.user,
                content=content
            )
            return redirect('listing', listing_id=listing.id)
        else:
            return HttpResponseBadRequest('Comment content is required.')
    
    return redirect('listing_detail', listing_id=listing.id)

@login_required
def close_listing(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    if listing.creator != request.user:
        return redirect('listing', listing_id=listing.id)  
    listing.active = False
    listing.save()

    return redirect('listing', listing_id=listing.id)

@login_required
def add_to_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    if not Watchlist.objects.filter(user=request.user, listing=listing).exists():
        Watchlist.objects.create(user=request.user, listing=listing)
        messages.success(request, "Item added to your watchlist.")
    else:
        messages.info(request, "This item is already in your watchlist.")
    return redirect('listing', listing_id=listing.id)

@login_required
def remove_from_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    watchlist_item = Watchlist.objects.filter(user=request.user, listing=listing).first()
    if watchlist_item:
        watchlist_item.delete()
        messages.success(request, "Item removed from your watchlist.")
    else:
        messages.info(request, "This item is not in your watchlist.")
    return redirect('listing', listing_id=listing.id)
