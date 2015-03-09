from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from rango.models import Category
from rango.models import Page
from rango.models import UserProfile
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm
from rango.forms import UserProfileForm
from rango.bing_search import run_query

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
    context_dict['result_list'] = None
    context_dict['query'] = None
    if request.method == 'POST':

        if request.POST['query']:
            query = request.POST['query'].strip()
            # Run our Bing function to get the results list!
            result_list = run_query(query)

            context_dict['result_list'] = result_list
            context_dict['query'] = query

    try:
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name
        pages = Page.objects.filter(category=category).order_by('-views')
        context_dict['pages'] = pages
        context_dict['category'] = category
        category.views = category.views + 1 # Increment views
        category.save();
        context_dict['views'] = category.views
        
        if not context_dict['query']:
            context_dict['query'] = category.name

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
    
def search(request):

    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'result_list': result_list})

def track_url(request):
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)

@login_required
def like_category(request):

    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        cat = Category.objects.get(id=int(cat_id))
        if cat:
            likes = cat.likes + 1
            cat.likes =  likes
            cat.save()

    return HttpResponse(likes)

# Helper function
def get_category_list(max_results=0, starts_with=''):
        cat_list = []
        if starts_with:
                cat_list = Category.objects.filter(name__istartswith=starts_with)

        if max_results > 0:
                if len(cat_list) > max_results:
                        cat_list = cat_list[:max_results]

        return cat_list
 
def suggest_category(request):
        cat_list = []
        starts_with = ''
        if request.method == 'GET':
                starts_with = request.GET['suggestion']

        cat_list = get_category_list(8, starts_with)

        return render(request, 'rango/cats.html', {'cats': cat_list })

@login_required
def register_profile(request):
    # A HTTP POST?
    if request.method == 'POST':
        form = UserProfileForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()

            return index(request)
        else:
            print form.errors
    else:
        form = UserProfileForm()

    return render(request, 'registration/profile_registration.html', {'form': form})

@login_required
def profile(request):
    context_dict = {}
    uprofile = UserProfile.objects.get(user = request.user)

    # A HTTP POST?
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        form.fields['website'].initial = uprofile.website
        context_dict['form'] = form
        context_dict['picture'] = uprofile.picture

        if form.is_valid():
            newprofile = form.save(commit=False)
            newprofile.user = request.user
            if 'picture' in request.FILES:
                newprofile.picture = request.FILES['picture']

            try:
                newprofile.save()
            except:
                uprofile.delete()
                newprofile.save()

            return index(request)
        else:
            print form.errors
    else:
        form = UserProfileForm()
        form.fields['website'].initial = uprofile.website
        context_dict['form'] = form
        context_dict['picture'] = uprofile.picture

    return render(request, 'rango/profile.html', context_dict)

def other_profile(request, username):
    if username == request.user.username:
        return profile(request)
    context_dict = {}
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse("No such username")

    uprofile = UserProfile.objects.get(user=user)
    context_dict['username'] = username
    context_dict['email'] = user.email
    context_dict['website'] = uprofile.website
    context_dict['picture'] = uprofile.picture
    return render(request, 'rango/other_profile.html', context_dict)

