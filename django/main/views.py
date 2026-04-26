from django.views.generic import DetailView
from django.db.models import Case, When, Value, IntegerField, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import User, Club, Membership, Event, Forum, ForumThread, ForumReply, DirectMessage, Announcement, ClubSettings, JoinRequest, Ban
from .forms import EventForm
from functools import wraps
import datetime
from datetime import date
from django.core.exceptions import ValidationError

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

        # Announcements: members see all, others see only 'everyone' visibility
        all_announcements = self.object.announcements.select_related('author').order_by('-created_at')
        if is_member:
            visible_announcements = all_announcements
        else:
            visible_announcements = all_announcements.filter(visibility=Announcement.EVERYONE)
        context["announcements"] = visible_announcements
        context["latest_announcement"] = visible_announcements.first()

        #Contacts: Members/Execs see all members, others only see the exec team
        exec_members = self.object.memberships.filter(
            role=Membership.EXECUTIVE
        ).select_related('user').order_by('user__first_name', 'user__last_name')

        general_members = self.object.memberships.filter(
            role=Membership.MEMBER
        ).select_related('user').order_by('user__first_name', 'user__last_name')

        context['exec_members'] = exec_members
        context['general_members'] = general_members

        is_saved = False
        if self.request.user.is_authenticated:
            is_saved = self.request.user.saved_clubs.filter(slug=self.object.slug).exists()
        context['is_saved'] = is_saved

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
        birthday_str = request.POST.get('birthday')
        if birthday_str:
            from datetime import date
            try:
                birthday = date.fromisoformat(birthday_str)
                today = date.today()
                age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
                if age > 118:
                    messages.error(request, 'Please enter a valid birthday. Age cannot exceed 118 years.')
                    return redirect('profile')
                if birthday > today:
                    messages.error(request, 'Birthday cannot be in the future.')
                    return redirect('profile')
                request.user.birthday = birthday
            except ValueError:
                messages.error(request, 'Invalid birthday format.')
                return redirect('profile')

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
    saved_clubs = request.user.saved_clubs.all()
    saved_slugs = set(saved_clubs.values_list('slug', flat=True))
    return render(request, 'main/profile.html', {
        'profile_user': request.user,
        'is_own_profile': True,
        'memberships': memberships,
        'rsvped_events': rsvped_events,
        'saved_clubs': saved_clubs,
        'saved_slugs': saved_slugs,
        'today': date.today(),
    })


def custom_404(request, exception=None):
    return render(request, 'main/404.html', status=404)


def user_profile_page(request, username):
    profile_user = get_object_or_404(User, username=username, is_user_admin=False)
    if request.user.is_authenticated and request.user.username == username:
        return redirect('profile')
    memberships = profile_user.memberships.select_related('club').filter(role__in=['member', 'executive'])
    rsvped_events = profile_user.rsvped_events.select_related('club').order_by('date', 'time')
    saved_slugs = set(request.user.saved_clubs.values_list('slug', flat=True)) if request.user.is_authenticated else set()
    return render(request, 'main/profile.html', {
        'profile_user': profile_user,
        'is_own_profile': False,
        'memberships': memberships,
        'rsvped_events': rsvped_events,
        'saved_slugs': saved_slugs,
    })


@login_required
def toggle_save_club(request, slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    club = get_object_or_404(Club, slug=slug)
    if request.user.saved_clubs.filter(slug=slug).exists():
        request.user.saved_clubs.remove(club)
        saved = False
    else:
        request.user.saved_clubs.add(club)
        saved = True
    return JsonResponse({'saved': saved})


def logout_page(request):
    logout(request)
    return redirect('home')


@login_required
def delete_account(request):
    if request.method != 'POST':
        return redirect('profile')
    password = request.POST.get('password', '')
    user = authenticate(username=request.user.username, password=password)
    if user is None:
        messages.error(request, 'Incorrect password. Account not deleted.')
        return redirect('profile')
    logout(request)
    user.delete()
    return redirect('home')


def google_signup(request):
    role = request.GET.get('role', 'member')
    request.session['signup_role'] = role
    return redirect('google_login')

def get_involved_page(request):
    query = request.GET.get('q', '').strip()
    clubs = Club.objects.all().order_by('name')
    if query:
        clubs = clubs.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    saved_slugs = set(request.user.saved_clubs.values_list('slug', flat=True)) if request.user.is_authenticated else set()
    return render(request, 'main/get_involved.html', {
        'clubs': clubs,
        'query': query,
        'saved_slugs': saved_slugs,
    })

def global_search(request):
    query = request.GET.get('q', '').strip()
    active_filter = request.GET.get('filter', 'all')

    users = User.objects.none()
    clubs = Club.objects.none()
    events = Event.objects.none()

    if query:
        users = User.objects.filter(is_user_admin=False).filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

        clubs = Club.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('name')

        events = Event.objects.select_related('club').filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(club__name__icontains=query)
        ).order_by('date', 'time')

    saved_slugs = set(request.user.saved_clubs.values_list('slug', flat=True)) if request.user.is_authenticated else set()
    return render(request, 'main/global_search.html', {
        'query': query,
        'users': users,
        'clubs': clubs,
        'events': events,
        'active_filter': active_filter,
        'saved_slugs': saved_slugs,
    })


@login_required
def user_suggest(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'users': []})
    users = User.objects.filter(is_user_admin=False).filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(pk=request.user.pk)[:8]
    return JsonResponse({'users': [
        {
            'username': u.username,
            'name': f'{u.first_name} {u.last_name}'.strip() or u.username,
            'email': u.email,
            'avatar': u.profile_picture.url if u.profile_picture else None,
        }
        for u in users
    ]})


def search_suggest(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'users': [], 'clubs': [], 'events': []})

    users = User.objects.filter(is_user_admin=False).filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:5]

    clubs = Club.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )[:5]

    events = Event.objects.select_related('club').filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(location__icontains=query)
    ).order_by('date')[:5]

    return JsonResponse({
        'users': [
            {'name': f'{u.first_name} {u.last_name}'.strip() or u.username,
             'username': u.username,
             'url': f'/users/{u.username}/'}
            for u in users
        ],
        'clubs': [
            {'name': c.name, 'url': f'/clubs/{c.slug}/'}
            for c in clubs
        ],
        'events': [
            {'title': e.title, 'date': e.date.strftime('%b %-d, %Y'), 'club': e.club.name, 'url': f'/events/{e.id}/'}
            for e in events
        ],
    })

@login_required
def join_club(request, slug):
    club = get_object_or_404(Club, slug=slug)

    if request.method == "POST":
        # Do not allow banned users to join
        if Ban.objects.filter(user=request.user, club=club).exists():
            messages.error(request, "You are banned from joining this club.")
            return redirect("club_detail", slug=slug)

        # If already a member, do nothing
        if Membership.objects.filter(user=request.user, club=club).exists():
            messages.info(request, "You are already a member of this club.")
            return redirect("club_detail", slug=slug)

        settings, _ = ClubSettings.objects.get_or_create(club=club)

        if settings.require_approval:
            JoinRequest.objects.get_or_create(
                user=request.user,
                club=club,
                status=JoinRequest.PENDING
            )
            messages.success(request, "Your join request has been submitted for approval.")
        else:
            Membership.objects.get_or_create(
                user=request.user,
                club=club,
                defaults={"role": Membership.MEMBER}
            )
            messages.success(request, f"You joined {club.name}.")

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
        user=request.user, club=club, role=Membership.EXECUTIVE
    ).exists()
    if not is_exec:
        return redirect('executive_page')
    if request.method == 'POST':
        event = Event()
        event.club = club
        event.created_by = request.user
        event.title = request.POST.get('title', '')
        event.description = request.POST.get('description', '')

        date_val = request.POST.get('date')
        if date_val:
            event.date = date_val

        end_date_val = request.POST.get('end_date')
        event.end_date = end_date_val if end_date_val else None

        start_time_val = request.POST.get('start_time')
        if start_time_val:
            event.start_time = start_time_val
        else:
            event.start_time = '00:00:00'

        event.time = event.start_time

        end_time_val = request.POST.get('end_time')
        event.end_time = end_time_val if end_time_val else None

        location_val = request.POST.get('location', '')
        event.location = location_val

        event.category = request.POST.get('category', '')

        if request.FILES.get('image'):
            event.image = request.FILES['image']

        event.save()
        return redirect('executive_club_events', slug=club.slug)

    return render(request, 'main/create_event.html', {'club': club})

def Events_page(request):
    events = Event.objects.all().order_by('-date','-start_time')  # fetch all events ordered by soonest first
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

@login_required
def post_announcement(request, slug):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(user=request.user, club=club, role=Membership.EXECUTIVE).exists()
    if not is_exec:
        return redirect('club_detail', slug=slug)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        visibility = request.POST.get('visibility', Announcement.EVERYONE)
        if visibility not in (Announcement.MEMBERS, Announcement.EVERYONE):
            visibility = Announcement.EVERYONE
        if content:
            Announcement.objects.create(
                club=club,
                author=request.user,
                title=title,
                content=content,
                visibility=visibility,
            )
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

# ──────────────────────────────────────────────
# EXEC VIEWS
# ──────────────────────────────────────────────

# This is for the executive page
@login_required
def executive_page(request):
    executive_memberships = request.user.memberships.filter(
        role=Membership.EXECUTIVE
    ).select_related('club')

    if not executive_memberships.exists():
        return render(request, 'main/executive_page.html', {
            'executive_memberships': executive_memberships,
            'dashboard_data': []
        })

    if executive_memberships.count() == 1:
        return redirect('executive_club_page', slug=executive_memberships.first().club.slug)

    return render(request, 'main/executive_page.html', {
        'executive_memberships': executive_memberships,
    })

@login_required
def executive_club_page(request, slug):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user, club=club, role=Membership.EXECUTIVE
    ).exists()
    if not is_exec:
        return redirect('executive_page')

    all_exec_clubs = Club.objects.filter(
        memberships__user=request.user,
        memberships__role=Membership.EXECUTIVE
    )
    upcoming_events = club.events.filter( # show the upcoming events
        date__gte=__import__('datetime').date.today()
    ).order_by('date', 'time')[:3]
    total_members = club.memberships.count()
    total_events = club.events.count()

    return render(request, 'main/executive_club_page.html', {
        'club': club,
        'all_exec_clubs': all_exec_clubs,
        'upcoming_events': upcoming_events,
        'total_members': total_members,
        'total_events': total_events,
    })

@login_required
def executive_club_people(request, slug):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user,
        club=club,
        role=Membership.EXECUTIVE
    ).exists() # check if they're exec
    if not is_exec:
        return redirect('executive_page')

    all_exec_clubs = Club.objects.filter(
        memberships__user=request.user,
        memberships__role=Membership.EXECUTIVE
    )
    #differentiate between exec and non-exec and order than by alphabetical order
    exec_members = club.memberships.filter(
        role=Membership.EXECUTIVE
    ).select_related('user').order_by(
        'user__first_name', 'user__last_name'
    )
    general_members = club.memberships.filter(
        role = Membership.MEMBER
    ).select_related('user').order_by(
        'user__first_name', 'user__last_name'
    )
    return render(request, 'main/executive_club_people.html', {
        'club': club,
        'all_exec_clubs': all_exec_clubs,
        'exec_members': exec_members,
        'general_members': general_members,
    })

@login_required
def executive_club_manage(request, slug):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user,
        club=club,
        role=Membership.EXECUTIVE
    ).exists() #check if they're exec
    if not is_exec:
        return redirect('executive_page')

    settings, _ = ClubSettings.objects.get_or_create(club=club)
    pending_requests = JoinRequest.objects.filter(club=club, status=JoinRequest.PENDING).select_related('user').order_by('created_at')
    general_members = club.memberships.filter(role=Membership.MEMBER).select_related('user').order_by('user__first_name', 'user__last_name')
    bans = Ban.objects.filter(club=club).select_related('user', 'banned_by').order_by('created_at')
    all_exec_clubs = Club.objects.filter(memberships__user=request.user, memberships__role=Membership.EXECUTIVE)

    return render(request, 'main/executive_club_manage.html', {
        'club': club,
        'settings': settings,
        'pending_requests': pending_requests,
        'general_members': general_members,
        'bans': bans,
        'all_exec_clubs': all_exec_clubs,
    })

@login_required
def executive_toggle_approval(request, slug):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user,
        club=club,
        role=Membership.EXECUTIVE
    ).exists()
    if not is_exec:
        return redirect('executive_page')
    if request.method == 'POST':
        settings, _ = ClubSettings.objects.get_or_create(club=club)
        #flip the current approval setting
        settings.require_approval = not settings.require_approval
        settings.save()
    return redirect('executive_club_manage', slug = slug)

@login_required
#This removes members from the club
def executive_remove_member(request, slug, membership_id):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user,
        club=club,
        role=Membership.EXECUTIVE
    ).exists()  # check if they're exec
    if not is_exec:
        return redirect('executive_page')
    if request.method == 'POST':
        membership = get_object_or_404(Membership, id=membership_id)
        if membership.user != request.user:
            membership.delete()
    return redirect('executive_club_people', slug = slug)

@login_required
def executive_handle_request(request, slug, request_id, action):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user,
        club=club,
        role=Membership.EXECUTIVE
    ).exists()
    if not is_exec:
        return redirect('executive_page')
    if request.method == 'POST':
        join_request = get_object_or_404(JoinRequest, id=request_id)
        if action == 'approve':
            join_request.status = JoinRequest.APPROVED
            join_request.save()
            membership = Membership.objects.get_or_create(user = join_request.user, club = club, defaults = {'role': Membership.MEMBER})
        elif action == 'reject':
            join_request.status = JoinRequest.REJECTED
            join_request.save()
        return redirect('executive_club_manage', slug = slug)

@login_required
def executive_ban_member(request, slug, membership_id):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user, club=club, role=Membership.EXECUTIVE
    ).exists()
    if not is_exec:
        return redirect('executive_page')
    if request.method == 'POST':
        membership = get_object_or_404(Membership, id=membership_id, club=club)
        # Prevent execs from banning themselves
        if membership.user != request.user:
            # get_or_create prevents duplicate bans
            Ban.objects.get_or_create(user=membership.user, club=club, defaults={'banned_by': request.user})
            membership.delete()
    return redirect('executive_club_manage', slug=slug)

@login_required
def executive_unban_member(request, slug, ban_id):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user, club=club, role=Membership.EXECUTIVE
    ).exists()
    if not is_exec:
        return redirect('executive_page')
    if request.method == 'POST':
        ban = get_object_or_404(Ban, id=ban_id, club=club)
        # Deleting the ban record lifts the ban
        ban.delete()
    return redirect('executive_club_manage', slug=slug)

#Club events for the exec
@login_required
def executive_club_events(request, slug):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user, club=club, role=Membership.EXECUTIVE
    ).exists()
    if not is_exec:
        return redirect('executive_page')
    #This helps to order the events by the latest
    today = datetime.date.today()
    upcoming = club.events.filter(date__gte=today).order_by('date', 'start_time')
    past = club.events.filter(date__lt=today).order_by('-start_time')
    events = list(upcoming) + list(past)
    return render(request, 'main/executive_club_events.html', {
        'club': club,
        'events': events,
    })
#Edit events
@login_required
def executive_edit_event(request, slug, event_id):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user, club=club, role=Membership.EXECUTIVE
    ).exists()
    if not is_exec:
        return redirect('executive_page')
    event = get_object_or_404(Event, id=event_id, club=club)
    if request.method == 'POST':
        event.title = request.POST.get('title') or event.title
        event.description = request.POST.get('description', '')

        date_val = request.POST.get('date')
        if date_val:
            event.date = date_val

        end_date_val = request.POST.get('end_date')
        event.end_date = end_date_val if end_date_val else None

        start_time_val = request.POST.get('start_time')
        if start_time_val:
            event.start_time = start_time_val

        event.time = event.start_time

        end_time_val = request.POST.get('end_time')
        event.end_time = end_time_val if end_time_val else None

        location_val = request.POST.get('location')
        if location_val:
            event.location = location_val

        event.category = request.POST.get('category', '')

        if request.FILES.get('image'):
            event.image = request.FILES['image']

        event.save()
        return redirect('executive_club_events', slug=club.slug)

    return render(request, 'main/executive_edit_event.html', {
        'club': club, 'event': event
    })
#Delete events
@login_required
def executive_delete_event(request, slug, event_id):
    club = get_object_or_404(Club, slug=slug)
    is_exec = Membership.objects.filter(
        user=request.user, club=club, role=Membership.EXECUTIVE
    ).exists()
    if not is_exec:
        return redirect('executive_page')
    event = get_object_or_404(Event, id=event_id, club=club)
    if request.method == 'POST':
        event.delete()
    return redirect('executive_club_events', slug=slug)

# ──────────────────────────────────────────────
# Event Details
# ──────────────────────────────────────────────
@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    is_rsvped = False
    if request.user.is_authenticated:
        is_rsvped = request.user in event.rsvps.all()

    attendees = event.rsvps.all()
    search_query = request.GET.get('q', '').strip()
    if search_query and request.user.is_authenticated:
        attendees = attendees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    return render(request, 'main/event_detail.html', {
        'event': event,
        'is_rsvped': is_rsvped,
        'attendees': attendees,
        'search_query': search_query,
    })

