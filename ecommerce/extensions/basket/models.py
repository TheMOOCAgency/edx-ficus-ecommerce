from django.db import models
from django.utils.translation import ugettext_lazy as _
from oscar.apps.basket.abstract_models import AbstractBasket
from oscar.core.loading import get_class

OrderNumberGenerator = get_class('order.utils', 'OrderNumberGenerator')
Selector = get_class('partner.strategy', 'Selector')

#MODIF HERE
import re

class Basket(AbstractBasket):
    site = models.ForeignKey(
        'sites.Site', verbose_name=_("Site"), null=True, blank=True, default=None, on_delete=models.SET_NULL
    )

    @property
    def order_number(self):
        return OrderNumberGenerator().order_number(self)

    ##all_lines(all_lines(
    #MODIF HERE TO GET THE MICROSITE
    def get_microsite_root_url(self):
        lines = self.all_lines()
        for line in lines:
            product_class_name = line.product.get_product_class().name
            if product_class_name == 'Seat' and "microsite_root_url:" in line.product.description and ":end_microsite_root_url" in line.product.description:
                return re.search('microsite_root_url:(.*):end_microsite_root_url', line.product.description).group(1)
            else:
                return None

    @classmethod
    def create_basket(cls, site, user):
        """ Create a new basket for the given site and user. """
        basket = cls.objects.create(site=site, owner=user)
        basket.strategy = Selector().strategy(user=user)
        return basket

    @classmethod
    def get_basket(cls, user, site):
        """Retrieve the basket belonging to the indicated user.

        If no such basket exists, create a new one. If multiple such baskets exist,
        merge them into one.
        """
        editable_baskets = cls.objects.filter(site=site, owner=user, status__in=cls.editable_statuses)
        if len(editable_baskets) == 0:
            basket = cls.create_basket(site, user)
        else:
            stale_baskets = list(editable_baskets)
            basket = stale_baskets.pop(0)
            for stale_basket in stale_baskets:
                # Don't add line quantities when merging baskets
                basket.merge(stale_basket, add_quantities=False)

        # Assign the appropriate strategy class to the basket
        basket.strategy = Selector().strategy(user=user)

        return basket

    def clear_vouchers(self):
        """Remove all vouchers applied to the basket."""
        for v in self.vouchers.all():
            self.vouchers.remove(v)

    def __unicode__(self):
        return _(u"{id} - {status} basket (owner: {owner}, lines: {num_lines})").format(
            id=self.id,
            status=self.status,
            owner=self.owner,
            num_lines=self.num_lines)


class BasketAttributeType(models.Model):
    """
    Used to keep attribute types for BasketAttribute
    """
    name = models.CharField(_("Name"), max_length=128, unique=True)

    def __unicode__(self):
        return self.name


class BasketAttribute(models.Model):
    """
    Used to add fields to basket without modifying basket directly.  Fields
    can be added by defining new types.  Currently only supports text fields,
    but could be extended
    """
    basket = models.ForeignKey('basket.Basket', verbose_name=_("Basket"), on_delete=models.CASCADE)
    attribute_type = models.ForeignKey(
        'basket.BasketAttributeType', verbose_name=_("Attribute Type"), on_delete=models.CASCADE
    )
    value_text = models.TextField(_("Text Attribute"))

    class Meta(object):
        unique_together = ('basket', 'attribute_type')


# noinspection PyUnresolvedReferences
from oscar.apps.basket.models import *  # noqa isort:skip pylint: disable=wildcard-import,unused-wildcard-import,wrong-import-position
