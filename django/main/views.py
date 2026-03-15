from django.views.generic import DetailView
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import User, Club, Membership, Event
from .forms import EventForm

class ClubDetailView(DetailView):
    model = Club
    template_name = "main/club_detail.html"
    context_object_name = "club"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        is_member = False
        is_exec = False

        if self.request.user.is_authenticated:

            membership = Membership.objects.filter(
                user=self.request.user,
                club=self.object
            ).first()

            if membership:
                is_member = True
                is_exec = membership.role == Membership.EXECUTIVE

        context["is_member"] = is_member
        context["is_exec"] = is_exec

        return context

def home(request):
    return render(request, 'main/home.html')

def signup_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        membership = request.POST.get('membership')

        if User.objects.filter(email=email).exists():
            return render(request, 'main/signup.html', {'error': 'An account with this email already exists.'})

        user = User(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        if hasattr(user, 'membership'):
            user.membership = membership
        user.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('create_profile')

    return render(request, 'main/signup.html')


def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            return render(request, 'main/login.html', {'error': 'Invalid email or password.'})

    return render(request, 'main/login.html')


def create_profile_page(request):
    if not request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        request.user.age = request.POST.get('age') or None
        request.user.birthday = request.POST.get('birthday') or None
        request.user.year = request.POST.get('year')
        request.user.school = request.POST.get('school')
        request.user.save()

        return redirect('profile')

    return render(request, 'main/create_profile.html')


def profile_page(request):
    #based on database
    memberships = request.user.memberships.select_related("club")
    if not request.user.is_authenticated:
        return redirect('home')
    return render(request, 'main/profile.html',{
        "memberships": memberships,
    })


def logout_page(request):
    logout(request)
    return redirect('home')


def google_signup(request):
    role = request.GET.get('role', 'member')
    request.session['signup_role'] = role
    return redirect('google_login')

def get_involved_page(request):
    query = request.GET.get('q', '').strip()
    clubs = Club.objects.all() #fetch all the club records from db
    if query:
        clubs = clubs.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    return render(request, 'main/get_involved.html', {
        'clubs': clubs, #pass clubs queryset to template
        'query': query,
    })

@login_required
def join_club(request, slug):
    if request.method == "POST":

        club = get_object_or_404(Club, slug=slug)

        Membership.objects.get_or_create(
            user=request.user,
            club=club,
            defaults={"role": Membership.MEMBER}
        )

    return redirect("club_detail", slug=slug)

@login_required
def verify_exec(request, slug):
    if request.method == "POST":

        club = get_object_or_404(Club, slug=slug)
        membership, created = Membership.objects.get_or_create(
            user=request.user,
            club=club
        )

        #update instead of new entry
        membership.role = Membership.EXECUTIVE
        membership.save()

    return redirect("club_detail", slug=slug)

def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        is_member = False

        if self.request.user.is_authenticated:
            is_member = Membership.objects.filter(
                user=self.request.user,
                club=self.object
            ).exists()

        context["is_member"] = is_member

        return context

@login_required
def executive_page(request):

    executive_memberships = request.user.memberships.filter(
        role=Membership.EXECUTIVE
    ).select_related("club")

    return render(request, "main/executive_page.html", {
        "executive_memberships": executive_memberships
    })

@login_required
def create_event(request, slug):

    club = get_object_or_404(Club, slug=slug)

    is_exec = Membership.objects.filter(
        user=request.user,
        club=club,
        role=Membership.EXECUTIVE
    ).exists()

    if not is_exec:
        return redirect("executive_page")

    if request.method == "POST":

        form = EventForm(request.POST)

        if form.is_valid():
            event = form.save(commit=False)

            event.club = club
            event.created_by = request.user

            event.save()

            return redirect("executive_page")

    else:
        form = EventForm()

    return render(request, "main/create_event.html", {
        "club": club,
        "form": form
    })