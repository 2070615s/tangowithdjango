from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm
from rango.forms import UserProfileForm

def index(request):
    request.session.set_test_cookie() # Test cookies
    category_list = Category.objects.order_by('-likes')[:5]
    pages_list = Page.objects.order_by('views')[:5]
    context_dict = {'categories': category_list, 'pages': pages_list}

    # Get number of visits to the site.
    visits = request.session.get("visits")
    if not visits:
        visits = 1
    reset_last_time_visit = False

    last_visit = request.session.get("last_visit")
    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")
        if (datetime.now() - last_visit_time).seconds > 0:
            visits = visits + 1
            reset_last_visit_time = True
    else:
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session["last_visit"] = str(datetime.now())
        request.session["visits"] = visits
    
    context_dict["visits"] = visits
    response = render(request, "rango/index.html", context_dict)
    return response

def about(request):
    if request.session.get("visits"):
        visits = request.session.get("visits")
    else:
        visits = 0
    return render(request, 'rango/about.html', {"visits": visits})

def category(request, category_name_slug):
    context_dict = {}
    try:
        category = Category.objects.get(slug=category_name_slug)
        context_dict["category_name"] = category.name
        pages = Page.objects.filter(category=category)
        context_dict["pages"] = pages
        context_dict["category"] = category
        context_dict["category_name_slug"] = category.slug
    except Category.DoesNotExist:
        pass
    
    return render(request, 'rango/category.html', context_dict)

@login_required
def add_category(request):
    if request.method == "POST": # Data has already been supplied, check and save it
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            return index(request) # Show homepage
        else:
            print form.errors
    else:
        form = CategoryForm() # Display form to enter details
    return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):
    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        cat = None

    if request.method == "POST":
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                return category(request, category_name_slug)
        else:
            print form.errors
    else:
        form = PageForm()

    context_dict = {'form': form, 'category': cat}
    return render(request, 'rango/add_page.html', context_dict)

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})

