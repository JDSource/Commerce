from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from .models import User, Listing, Bid, Comment
from .forms import BidForm, CommentForm, ListingForm
from django.urls import reverse
from django.contrib import messages
from django.db.models import Count



def index(request):
    active_listings = Listing.objects.filter(is_active=True)
    return render(request, "auctions/index.html", {
        "listings": active_listings
})

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
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

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
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
    
# allows user to create a listing (listings form logic)
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.is_active = True
            listing.save()
            return redirect('index')
    else:
        form = ListingForm()
    return render(request, 'auctions/create_listing.html', {'form': form})

    

# displays the listing, posts bids, posts comments
def listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    bid_form = BidForm()
    comment_form = CommentForm()
    comments = Comment.objects.filter(listing=listing)
    bids = Bid.objects.filter(listing=listing).order_by('-bid_amount')

    if request.method == "POST":
        if "bid_amount" in request.POST:
            bid_form = BidForm(request.POST)
            if bid_form.is_valid():
                bid_amount = bid_form.cleaned_data["bid_amount"]
                if bid_amount > (listing.currentbid or listing.startingbid):
                    bid = bid_form.save(commit=False)
                    bid.listing = listing
                    bid.bidder = request.user
                    bid.save()
                    listing.currentbid = bid_amount
                    listing.save()
                    messages.success(request,"Your bid is now live!")
                    return redirect('listing', listing_id=listing.id)
                else:
                    messages.error(request,"Your bid must be higher than the current or starting bid.")
                    return redirect('listing', listing_id=listing.id)
        elif "comment_text" in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.listing = listing
                comment.commenter = request.user
                comment.save()
                messages.success(request,"Your comment has been posted!")
                return redirect('listing', listing_id=listing.id)

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bid_form": bid_form,
        "comment_form": comment_form,
        "comments": comments,
         "bids": bids
    })
    
# watchlist
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    user = request.user

    if user.is_authenticated:
        if listing in user.watchlist.all():
            user.watchlist.remove(listing)
            messages.success(request, "The listing was removed from your watchlist.")
        else:
            user.watchlist.add(listing)
            messages.success(request, "The listing was added to your watchlist.")
        return redirect('watchlist')

    else:
        messages.error(request, "You need to sign in to manage your watchlist.")
        return redirect('listing', listing_id=listing_id)


#view watchlist
def watchlist(request):
    user = request.user
    watchlist_items = user.watchlist.all()
    return render(request, "auctions/watchlist.html", {
        'watchlist_items': watchlist_items
    })

#close auction
def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if request.user != listing.owner:
        messages.error(request, "You are not authorized to close this auction.")
        return redirect('listing', listing_id=listing_id)
    
    listing.close_auction()
    messages.success(request, "The auction was closed successfully.")
    return redirect('listing', listing_id=listing_id)

#categories
def categories(request):
    categories = Listing.objects.filter(is_active=True).values('category').annotate(total=Count('category')).order_by('category')
    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def category_listings(request, category_name):
    listings = Listing.objects.filter(category=category_name, is_active=True)
    return render(request, "auctions/category_listings.html", {
        "listings": listings,
        "category_name": category_name
    })
