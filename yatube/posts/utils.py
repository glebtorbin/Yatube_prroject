from django.core.paginator import Paginator

POSTS_ON_PAGE: int = 10


def paginate(request, obj):
    paginator = Paginator(obj, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
