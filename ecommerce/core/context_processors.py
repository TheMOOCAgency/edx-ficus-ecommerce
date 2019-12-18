from ecommerce.core.url_utils import get_lms_dashboard_url, get_lms_url
from ecommerce.extensions.basket.models import Basket
from ecommerce.extensions.catalogue.models import Product
from ecommerce.courses.models import Course

import re
import logging
log = logging.getLogger()


def core(request):
    all_lines = Basket.objects.get(id=request.basket.id).all_lines()
    product = Product.objects.get(id=all_lines[0].product_id)
    course = Course.objects.get(id=product.course_id)
    parent_product = Product.objects.get(course=product.course_id, structure='parent')
    microsite_url = ''
    if re.search('microsite_root_url:(.*):end_microsite_root_url', parent_product.description) is not None:
        microsite_url = re.search('microsite_root_url:(.*):end_microsite_root_url', parent_product.description).group(1)
    language = request.LANGUAGE_CODE
    try:
        language = request.COOKIES['tma_pref_lang']
    except:
        pass

    return {
        'lms_base_url': get_lms_url(),
        'lms_dashboard_url': get_lms_dashboard_url(),
        'platform_name': request.site.name,
        'support_url': request.site.siteconfiguration.payment_support_url,
        'microsite_url': microsite_url,
        'parent_product': parent_product,
        'cookie_lang': language
    }
