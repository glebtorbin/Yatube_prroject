from django.core.paginator import Paginator


def paginate(request, obj):
    paginator = Paginator(obj, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
