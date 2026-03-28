from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .models import User,Club, Event, Membership
from .models import User, Club, Membership, Event, Thread, ThreadMessage, DirectMessage
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages


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
    if not request.user.is_authenticated:
        return redirect('home')
    return render(request, 'main/profile.html')


def logout_page(request):
    logout(request)
    return redirect('home')


def google_signup(request):
    role = request.GET.get('role', 'member')
    request.session['signup_role'] = role
    return redirect('google_login')

def get_involved_page(request):
    clubs = Club.objects.all() #fetch all the club records from db
    return render(request, 'main/get_involved.html', {
        'clubs': clubs #pass clubs queryset to template
    })

def my_clubs_page(request):
    memberships = Membership.objects.filter(user=request.user)
    return render(request, 'main/my_clubs.html', {'memberships': memberships})

def Events_page(request):
    events = Event.objects.all().order_by('date')
    return render(request, 'main/Events.html', {'events': events})

# ──────────────────────────────────────────────
# MESSAGING VIEWS
# ──────────────────────────────────────────────

@login_required
def thread_list(request, slug):
    """Show all threads for a club. Members can see them; non-members cannot."""
    club = get_object_or_404(Club, slug=slug)

    membership = Membership.objects.filter(user=request.user, club=club).first()
    if not membership:
        return redirect('club_detail', slug=slug)

    is_exec = membership.role == Membership.EXECUTIVE
    threads = Thread.objects.filter(club=club).order_by('-created_at')

    return render(request, 'main/thread_list.html', {
        'club': club,
        'threads': threads,
        'is_exec': is_exec,
    })


@login_required
def thread_detail(request, slug, thread_id):
    """View a thread and post a reply."""
    club = get_object_or_404(Club, slug=slug)
    thread = get_object_or_404(Thread, id=thread_id, club=club)

    membership = Membership.objects.filter(user=request.user, club=club).first()
    if not membership:
        return redirect('club_detail', slug=slug)

    is_exec = membership.role == Membership.EXECUTIVE

    # Announcement threads: only execs can post; everyone can read
    can_post = is_exec if thread.is_announcement else True

    if request.method == 'POST' and can_post:
        content = request.POST.get('content', '').strip()
        if content:
            ThreadMessage.objects.create(
                thread=thread,
                sender=request.user,
                content=content,
            )
        return redirect('thread_detail', slug=slug, thread_id=thread_id)

    pinned = thread.messages.filter(is_pinned=True)
    regular = thread.messages.filter(is_pinned=False)

    return render(request, 'main/thread_detail.html', {
        'club': club,
        'thread': thread,
        'pinned_messages': pinned,
        'regular_messages': regular,
        'is_exec': is_exec,
        'can_post': can_post,
    })


@login_required
def create_thread(request, slug):
    """Create a new thread in a club. Executives can mark it as announcement."""
    club = get_object_or_404(Club, slug=slug)

    membership = Membership.objects.filter(user=request.user, club=club).first()
    if not membership:
        return redirect('club_detail', slug=slug)

    is_exec = membership.role == Membership.EXECUTIVE

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        is_announcement = request.POST.get('is_announcement') == 'on' and is_exec
        if title:
            Thread.objects.create(
                club=club,
                title=title,
                created_by=request.user,
                is_announcement=is_announcement,
            )
        return redirect('thread_list', slug=slug)

    return render(request, 'main/create_thread.html', {
        'club': club,
        'is_exec': is_exec,
    })


@login_required
def pin_message(request, slug, thread_id, message_id):
    """Toggle pin on a message. Officers only."""
    club = get_object_or_404(Club, slug=slug)

    is_exec = Membership.objects.filter(
        user=request.user, club=club, role=Membership.EXECUTIVE
    ).exists()

    if is_exec and request.method == 'POST':
        message = get_object_or_404(ThreadMessage, id=message_id, thread__club=club)
        message.is_pinned = not message.is_pinned
        message.save()

    return redirect('thread_detail', slug=slug, thread_id=thread_id)


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