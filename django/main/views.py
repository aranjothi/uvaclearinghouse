from django.views.generic import DetailView
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import User, Club, Membership, Event, Forum, ForumThread, ForumReply, DirectMessage
from .forms import EventForm
from functools import wraps

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
        user_role = None
        if self.request.user.is_authenticated:
            membership = Membership.objects.filter(
                user=self.request.user,
                club=self.object
            ).first()
            if membership:
                is_member = True
                is_exec = membership.role == Membership.EXECUTIVE
                user_role = membership.get_role_display()
        context["is_member"] = is_member
        context["is_exec"] = is_exec
        context["user_role"] = user_role
        forum, _ = Forum.objects.get_or_create(club=self.object)
        context["forum"] = forum
        context["threads"] = forum.threads.select_related('author').order_by('-created_at')[:20]
        events = list(self.object.events.order_by('date', 'time'))
        rsvped_ids = set()
        if self.request.user.is_authenticated:
            rsvped_ids = set(self.request.user.rsvped_events.values_list('id', flat=True))
        context["events"] = events
        context["rsvped_ids"] = rsvped_ids
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
    if request.user.is_user_admin:
        return redirect('user_admin')
    if request.method == 'POST':
        request.user.age = request.POST.get('age') or None
        request.user.birthday = request.POST.get('birthday') or None
        request.user.year = request.POST.get('year')
        request.user.school = request.POST.get('school')
        if request.FILES.get('profile_picture'):
            request.user.profile_picture = request.FILES['profile_picture']
        request.user.save()
        return redirect('profile')
    return render(request, 'main/create_profile.html')


def profile_page(request):
    if not request.user.is_authenticated:
        return redirect('home')
    if request.user.is_user_admin:
        return redirect('user_admin')
    memberships = request.user.memberships.select_related("club")
    rsvped_events = request.user.rsvped_events.select_related('club').order_by('date', 'time')
    return render(request, 'main/profile.html', {"memberships": memberships, "rsvped_events": rsvped_events})


def logout_page(request):
    logout(request)
    return redirect('home')


def google_signup(request):
    role = request.GET.get('role', 'member')
    request.session['signup_role'] = role
    return redirect('google_login')

def get_involved_page(request):
    query = request.GET.get('q', '').strip()
    clubs = Club.objects.all().order_by('name') # fetch all club records from db and alphabetical order
    if query:
        clubs = clubs.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    return render(request, 'main/get_involved.html', {
        'clubs': clubs,  # pass clubs queryset to template
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
        entered_code = request.POST.get('executive_code', '').strip()
        if entered_code == club.executive_code:
            membership, _ = Membership.objects.get_or_create(
                user=request.user,
                club=club,
                defaults={"role": Membership.MEMBER}
            )
            membership.role = Membership.EXECUTIVE
            membership.save()
            messages.success(request, f"You are now an executive member of {club.name}.")
        else:
            messages.error(request, "Invalid executive code.")
    return redirect("club_detail", slug=slug)

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
            return redirect("club_detail", slug=club.slug)
    else:
        form = EventForm()
    return render(request, "main/create_event.html", {"club": club, "form": form})

def Events_page(request):
    events = Event.objects.all().order_by('date')  # fetch all events ordered by soonest first
    return render(request, 'main/Events.html', {'events': events})  # pass events to template

@login_required
def my_clubs_page(request):
    memberships = Membership.objects.filter(user=request.user)  # get all memberships for current user
    return render(request, 'main/my_clubs.html', {'memberships': memberships})

def members_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not Membership.objects.filter(user=request.user).exists():
            return redirect('get_involved')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def forum_list(request, slug):
    club = get_object_or_404(Club, slug=slug)
    if not Membership.objects.filter(user=request.user, club=club).exists():
        return redirect('get_involved')
    forum, _ = Forum.objects.get_or_create(club=club) #create forum
    threads = forum.threads.all().order_by('-created_at') #new threads
    return render(request, 'main/forum_list.html', {'club': club, 'threads': threads, 'forum': forum})

@login_required
def forum_new_thread(request, slug):
    club = get_object_or_404(Club, slug=slug)
    if not Membership.objects.filter(user=request.user, club=club).exists():
        return redirect('get_involved')
    if request.method == "POST":
        title = request.POST.get('title')
        content = request.POST.get('content')
        forum, _ = Forum.objects.get_or_create(club=club)
        ForumThread.objects.create(forum=forum, title=title, content=content, author=request.user)
        return redirect("forum_list", slug=slug)
    return render(request, 'main/forum_new_thread.html', {'club': club})

@login_required
def forum_thread(request, slug, thread_id):
    club = get_object_or_404(Club, slug=slug)
    if not Membership.objects.filter(user=request.user, club=club).exists():
        return redirect('get_involved')
    thread = get_object_or_404(ForumThread, id=thread_id)
    replies = thread.replies.all().order_by('created_at') #oldest replies first
    if request.method == 'POST':
        content = request.POST.get('content') #this handles new replies
        ForumReply.objects.create(thread=thread, content=content, author=request.user)
        return redirect('forum_thread', slug=slug, thread_id=thread_id)
    return render(request, 'main/forum_thread.html', {'club': club, 'thread': thread, 'replies': replies})

@login_required
def like_thread(request, slug, thread_id):
    thread = get_object_or_404(ForumThread, id=thread_id)
    if request.user in thread.likes.all():
        thread.likes.remove(request.user)  # remove like
    else:
        thread.likes.add(request.user)
    return redirect('forum_thread', slug=slug, thread_id=thread.id)

@login_required
def like_reply(request, slug, reply_id):
    reply = get_object_or_404(ForumReply, id=reply_id)
    if request.user in reply.likes.all():
        reply.likes.remove(request.user) #toggle likes on the replies
    else:
        reply.likes.add(request.user)
    return redirect('forum_thread', slug=slug, thread_id=reply.thread.id)
    events = Event.objects.all().order_by('date')
    return render(request, 'main/Events.html', {'events': events})

@login_required
def rsvp_event(request, event_id):
    from .models import Event
    event = get_object_or_404(Event, id=event_id)
    if request.user in event.rsvps.all():
        event.rsvps.remove(request.user)
    else:
        event.rsvps.add(request.user)
    return redirect('club_detail', slug=event.club.slug)

@login_required
def upload_club_image(request, slug):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(user=request.user, club=club, role=Membership.EXECUTIVE).exists()
    if not is_exec:
        return redirect('club_detail', slug=slug)
    if request.method == 'POST' and request.FILES.get('club_image'):
        club.image = request.FILES['club_image']
        club.save()
    return redirect('club_detail', slug=slug)

# ──────────────────────────────────────────────
# USER ADMIN VIEWS
# ──────────────────────────────────────────────

@login_required
def user_admin(request):
    if not request.user.is_user_admin:
        return redirect('home')
    users = User.objects.filter(is_user_admin=False).prefetch_related('memberships__club').order_by('email')
    return render(request, 'main/user_admin.html', {'users': users})

@login_required
def user_admin_change_role(request):
    if not request.user.is_user_admin:
        return redirect('home')
    if request.method == 'POST':
        membership_id = request.POST.get('membership_id')
        new_role = request.POST.get('role')
        if new_role in (Membership.MEMBER, Membership.EXECUTIVE):
            membership = get_object_or_404(Membership, id=membership_id)
            membership.role = new_role
            membership.save()
    return redirect('user_admin')

# ──────────────────────────────────────────────
# MESSAGING VIEWS
# ──────────────────────────────────────────────


@login_required
def dm_inbox(request):
    """Show all unique DM conversations the current user is part of."""
    user = request.user

    # Get all users who have exchanged DMs with the current user
    from django.db.models import Max, Q as DjangoQ

    sent_to = DirectMessage.objects.filter(sender=user).values_list('recipient', flat=True).distinct()
    received_from = DirectMessage.objects.filter(recipient=user).values_list('sender', flat=True).distinct()

    # Combine both sets of user IDs
    convo_user_ids = set(list(sent_to) + list(received_from))
    convo_users = User.objects.filter(id__in=convo_user_ids)

    # Count unread messages per conversation partner
    unread_counts = {}
    for u in convo_users:
        unread_counts[u.id] = DirectMessage.objects.filter(
            sender=u, recipient=user, is_read=False
        ).count()

    return render(request, 'main/dm_inbox.html', {
        'convo_users': convo_users,
        'unread_counts': unread_counts,
    })

@login_required
def dm_conversation(request, username):
    """View and send DMs with a specific user."""
    other_user = User.objects.filter(
        Q(username=username) | Q(email__iexact=username)
    ).first()

    if not other_user:
        messages.error(request, 'That email does not exist. Please try again.')
        return redirect('dm_inbox')

    if other_user == request.user:
        return redirect('dm_inbox')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            DirectMessage.objects.create(
                sender=request.user,
                recipient=other_user,
                content=content,
            )
        return redirect('dm_conversation', username=username)

    DirectMessage.objects.filter(
        sender=other_user, recipient=request.user, is_read=False
    ).update(is_read=True)

    chat_messages = DirectMessage.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('created_at')

    return render(request, 'main/dm_conversation.html', {
        'other_user': other_user,
        'messages': chat_messages,
    })


@login_required
def widget_inbox(request):
    user = request.user
    sent_to = DirectMessage.objects.filter(sender=user).values_list('recipient', flat=True).distinct()
    received_from = DirectMessage.objects.filter(recipient=user).values_list('sender', flat=True).distinct()
    convo_user_ids = set(list(sent_to) + list(received_from))
    convo_users = User.objects.filter(id__in=convo_user_ids)
    data = []
    for u in convo_users:
        unread = DirectMessage.objects.filter(sender=u, recipient=user, is_read=False).count()
        last_msg = DirectMessage.objects.filter(
            Q(sender=user, recipient=u) | Q(sender=u, recipient=user)
        ).order_by('-created_at').first()
        data.append({
            'username': u.username,
            'name': f"{u.first_name} {u.last_name}".strip() or u.email,
            'unread': unread,
            'last_message': last_msg.content if last_msg else '',
            'last_time': last_msg.created_at.strftime('%b %d, %H:%M') if last_msg else '',
        })
    data.sort(key=lambda x: x['last_time'], reverse=True)
    return JsonResponse({'conversations': data})


@login_required
def widget_conversation(request, username):
    other_user = User.objects.filter(
        Q(username=username) | Q(email__iexact=username)
    ).first()
    if not other_user:
        return JsonResponse({'error': 'User not found'}, status=404)
    DirectMessage.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)
    chat_messages = DirectMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('created_at').values('content', 'created_at', 'sender__username')
    return JsonResponse({
        'messages': [
            {
                'content': m['content'],
                'mine': m['sender__username'] == request.user.username,
                'time': m['created_at'].strftime('%b %d, %H:%M'),
            }
            for m in chat_messages
        ],
        'name': f"{other_user.first_name} {other_user.last_name}".strip() or other_user.email,
    })


@login_required
def widget_send(request):
    if request.method == 'POST':
        import json
        body = json.loads(request.body)
        username = body.get('username', '').strip()
        content = body.get('content', '').strip()
        other_user = User.objects.filter(
            Q(username=username) | Q(email__iexact=username)
        ).first()
        if not other_user:
            return JsonResponse({'error': 'User not found'}, status=404)
        if not content:
            return JsonResponse({'error': 'Empty message'}, status=400)
        DirectMessage.objects.create(sender=request.user, recipient=other_user, content=content)
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'POST only'}, status=405)
