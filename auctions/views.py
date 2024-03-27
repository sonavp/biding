from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.db.models import Max
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import TemplateView

from .models import User, Listing, Watchlist, Bid, Comment

class BidForm(forms.Form):
    bid_form = forms.IntegerField(required=True, label='Create your bid')
    bid_form.widget.attrs.update({'class': 'form-control'})

class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(), label='Leave a comment')
    comment.widget.attrs.update({
        'class': 'form-control',
        'rows': '3'
    })

class IndexView(TemplateView):
    template_name = "auctions/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_categories"] = Listing.objects.values('category').distinct().exclude(category__exact='')
        context["listings"] = Listing.objects.all()
        return context

class LoginView(View):
    def get(self, request):
        return render(request, "auctions/login.html")

    def post(self, request):
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

class LogoutView(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse("index"))

class RegisterView(View):
    def get(self, request):
        return render(request, "auctions/register.html")

    def post(self, request):
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

class CreateListingView(View):
    def get(self, request):
        return render(request, "auctions/create_listing.html")

    def post(self, request):
        name = request.POST["name"]
        category = request.POST['category']
        starting_bid = request.POST["starting_bid"]
        description = request.POST["description"]
        url = request.POST["url"]
        owner = request.POST['owner']
        user_owner = User.objects.get(username=owner)

        try:
            Listings_created = Listing(name=name, category=category, starting_bid=starting_bid, description=description, url=url, owner=user_owner)
            Listings_created.save()
            return HttpResponseRedirect(reverse("index"))
        except IntegrityError:
            return render(request, "auctions/create_listing.html", {
                "message": "Listing not created."
            })

class ActiveListingView(View):
    def get(self, request, listing_id):
        try:
            listing = Listing.objects.get(id=listing_id)
            curent_user = request.user.id
            bid_count = Bid.objects.filter(item_bid=listing_id).count()

            if bid_count > 0:
                max_bid = Bid.objects.filter(item_bid=listing_id).aggregate(Max('bid'))
                max_bid = max_bid['bid__max']
            else:
                max_bid = listing.starting_bid

            if Watchlist.objects.filter(user_watchlist=curent_user, listing_item=listing_id).exists():
                watchlist_state = False
            else:
                watchlist_state = True

        except Listing.DoesNotExist:
            raise Http404("Listing not found.")

        comments = Comment.objects.filter(listing_comment=listing_id)

        return render(request, "auctions/active_listing.html", {
            "listing": listing,
            'comments': comments,
            'watchlist_state': watchlist_state,
            'bid_count': bid_count,
            'max_bid': max_bid,
            'form': BidForm(),
            'comment_form': CommentForm()
        })

    def post(self, request, listing_id):
        curent_user = request.user
        listing = Listing.objects.get(id=listing_id)
        form = BidForm(request.POST)
        if form.is_valid():
            current_bid = form.cleaned_data['bid_form']
            bid_count = Bid.objects.filter(item_bid=listing_id).count()
            max_bid = Bid.objects.filter(item_bid=listing_id).aggregate(Max('bid'))
            max_bid = max_bid['bid__max'] if max_bid['bid__max'] else listing.starting_bid

            if current_bid > max_bid:
                bid = Bid(user_bid=curent_user, item_bid=listing, bid=current_bid)
                bid.save()
                return HttpResponseRedirect(reverse("active_listing", args=(listing_id,)))
            else:
                return render(request, "auctions/active_listing.html", {
                    "listing": listing,
                    'comments': Comment.objects.filter(listing_comment=listing_id),
                    'watchlist_state': Watchlist.objects.filter(user_watchlist=curent_user, listing_item=listing).exists(),
                    'bid_count': bid_count,
                    'max_bid': max_bid,
                    'form': BidForm(),
                    'comment_form': CommentForm(),
                    "err_message": "Bid must be greater than current max bid."
                })
        else:
            return render(request, "auctions/active_listing.html", {
                "listing": listing,
                'comments': Comment.objects.filter(listing_comment=listing_id),
                'watchlist_state': Watchlist.objects.filter(user_watchlist=curent_user, listing_item=listing).exists(),
                'bid_count': bid_count,
                'max_bid': max_bid,
                'form': BidForm(),
                'comment_form': CommentForm(),
                "err_message": "Invalid bid amount."
            })

class WatchlistView(View):
    def get(self, request):
        curent_user = request.user
        curent_watchlist = Watchlist.objects.filter(user_watchlist=curent_user)
        return render(request, "auctions/watchlist.html", {
            "all_watchlists": curent_watchlist
        })

    def post(self, request):
        curent_user = request.user
        listing_id = request.POST.get("listing_id")
        listing_item = Listing.objects.get(id=listing_id)
        if Watchlist.objects.filter(user_watchlist=curent_user, listing_item=listing_item).exists():
            Watchlist.objects.filter(user_watchlist=curent_user, listing_item=listing_item).delete()
        else:
            Watchlist.objects.create(user_watchlist=curent_user, listing_item=listing_item)
        return HttpResponseRedirect(reverse("watchlist"))

class CloseBidView(View):
    def post(self, request):
        listing_id = request.POST.get("listing_id")
        listing = Listing.objects.get(id=listing_id)
        bid_count = Bid.objects.filter(item_bid=listing_id).count()
        if bid_count > 0:
            max_bid = Bid.objects.filter(item_bid=listing_id).aggregate(Max('bid'))['bid__max']
            bid_winner = Bid.objects.get(item_bid=listing_id, bid=max_bid)
            listing.winner = bid_winner.user_bid
        else:
            listing.winner = None
        listing.active = False
        listing.save()
        return HttpResponseRedirect(reverse("index"))

class CommentView(View):
    def post(self, request):
        curent_user = request.user
        listing_id = request.POST.get("listing_id")
        listing_item = Listing.objects.get(id=listing_id)
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.cleaned_data['comment']
            Comment.objects.create(user_comment=curent_user, listing_comment=listing_item, comment=comment)
            return HttpResponseRedirect(reverse("active_listing", args=(listing_id,)))
        else:
            return HttpResponseBadRequest("Invalid comment.")

class CategoryView(View):
    def get(self, request, category):
        listing_category = Listing.objects.filter(category=category)
        return render(request, "auctions/category.html", {
            'category': category,
            'listing_category': listing_category
        })
