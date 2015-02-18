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
    return render(request, 'rango/about.html', {})

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

def register(request):
    # Test cookies
    if request.session.test_cookie_worked():
        print ">>>> TEST COOKIE WORKED!"
        request.session.delete_test_cookie()

    registered = False

    if request.method == "POST":
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password) # Hash
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True
        else:
            print user_form.errors, profile_form.errors

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    context_dict = {'user_form': user_form, 'profile_form': profile_form, 'registered': registered}
    return render(request, 'rango/register.html', context_dict)

def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse("Rango account is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    else:
        return render(request, 'rango/login.html', {})

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')
