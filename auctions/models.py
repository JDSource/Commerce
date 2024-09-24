from django.contrib.auth.models import AbstractUser, User
from django.db import models


class User(AbstractUser):
    watchlist = models.ManyToManyField('Listing', blank=True, related_name='watched_by')

class Listing(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=64)
    image_url = models.URLField(null=True, blank=True)
    startingbid = models.DecimalField(max_digits=10, decimal_places=2)
    currentbid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    is_active = models.BooleanField(default=True)
    winner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="won_auctions")

    def close_auction(self):
        """Close the auction and set the highest bidder as winner."""
        if self.currentbid is not None:
            highest_bid = self.bids.order_by('-bid_amount').first()
            if highest_bid:
                self.winner = highest_bid.bidder
        self.is_active = False
        self.save()

    def __str__(self):
        return f"{self.title} ({self.category}) - {self.startingbid}"
    

class Bid(models.Model):
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bid_amount} on {self.listing.title} by {self.bidder.username}"
    

class Comment(models.Model):
    comment_text = models.TextField()
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commenter.username} on {self.listing.title}"
    


