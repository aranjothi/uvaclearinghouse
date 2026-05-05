# CIO Clearinghouse (Team B-05)

This is a CIO Clearinghouse web application designed to help students discover and connect with CIOs, and help organization leaders promote their clubs and events.

## Description

The CIO Clearinghouse application is designed to improve how students discover and engage with student organizations (CIOs). The platform provides a centralized space where students can explore clubs, view upcoming events, and join organizations that match their interests.

Users can browse detailed club profiles, search for organizations, and RSVP to events. The application also allows students to save clubs and communicate with other users through a built-in messaging system.

For organization leaders, the platform provides tools to manage their clubs, verify executive roles using secure codes, and promote events to a wider audience. This helps streamline communication and improve visibility for student organizations.

Overall, the system enhances the connection between students and CIOs by making information more accessible and interaction more efficient.

## Live Application

https://hooslinked-07883ee36d63.herokuapp.com/

*Note: For the ads to be visible and interactable, the user must have any adblockers disabled. Uploading ad images to the executive dashboard will still function properly, viewing is just restricting with adblocker usage. In some browsers, you may need to disable your adblocker to see the entire profile and inbox pages, so take action accordingly.*

**Executive Codes**

To gain access to executive permissions of a club, you must verify using a code. Below are the codes for all the clubs on the application:

- Mind&Body at UVA: 4c9c2b06
- Asambé (formerly known as Afro-Hoos): 33957149
- Community Alliance of South Americans: 2c60c3d3
- Aero Design Team at UVa/Hoos Flying: 998f1d1a
- The Occultation Group: 24ab9c6d
- Biomedical Engineering Society: f65f14cb
- APEX Dance Crew: d6ef7c11
- Accounting Society at McIntire: 866bbc85
- A Moment of Magic at UVA: 87550d2a
- 3D Printing Club at The University of Virginia: 391c79a1
- Charlottesville Book Club: d5b701e7

**User Administrator**

To see the user administrator panel, you need login information. Use the following login info to gain access:

- User (email): aranadmin@example.com
- Password: oregonftw349

**Django Administrator Panel**

If you need to see the database for any reason, navigate to https://hooslinked-07883ee36d63.herokuapp.com/admin/login/?next=/admin/ and use the following login:

- Username: aranj
- Password: aran

## Navigating the Website

The live application at https://hooslinked-07883ee36d63.herokuapp.com/ supports three types of users:

**General users** — create an account, browse clubs on the Clubs page, view club profiles (highlights, announcements, events, discussions), join clubs, RSVP to events, save clubs, message other users, and manage your profile.

**Executive members** — after joining a club, verify your executive role using the club's code (see codes above). This unlocks an Exec EZ-Access panel on the club page for posting announcements, creating events, editing club info, and uploading media. The full executive dashboard (`/executives/`) gives access to event management, member contacts, club management (approvals, bans), documents, and ads.

**User admins** — created via the Django admin panel; can view all users and change membership roles site-wide. you can find 

## Navigating the Codebase

The Django app lives in `django/`. Key locations:

- **Models** — `django/main/models.py` — All database models (`User`, `Club`, `Membership`, `Event`, `Announcement`, `PollOption`, `PollVote`, `DirectMessage`, `Highlight`, `ClubAd`, `ClubDocument`, etc.)
- **Views** — `django/main/views.py` — All view functions and the `ClubDetailView` class-based view
- **URLs** — `django/main/urls.py` — All URL patterns
- **Templates** — `django/main/templates/main/` — One HTML file per page; exec dashboard pages are prefixed `executive_`
- **Static assets** — `django/main/assets/` — Images and icons served via WhiteNoise
- **Migrations** — `django/main/migrations/` — Database migration history
- **Settings** — `django/clearinghouse/settings.py` — Django settings including S3, auth, and database config
- **OAuth adapters** — `django/main/adapters.py` — Custom allauth adapters for Google sign-in

## Authors

- Audrey Bediako  
- Aran Jothi  
- Yoyo Ni  
- Love Joshi  
- Peter Nenyuk  

## Team

Team B-05

## AI Usage

This project used Claude (by Anthropic) as an AI coding assistant throughout development. Key example areas where Claude was used include:

- **Direct messaging system** — Chat widget, inbox, and conversation views with real-time JSON API endpoints
- **Announcements and polls** — Post/vote/unvote/delete flow, poll percentage rendering, and syncing between the latest-announcement preview and the tab
- **Club highlights** — Image upload, drag-to-reorder, lightbox viewer, and caption management
- **Club management features** — Join request approval flow, ban/unban, member removal, and the `ClubSettings` model
- **Executive dashboard** — The full sidebar layout, events management pages, and the edit event form
- **Global search** — Live suggest API and the search results page
- **Google OAuth integration** — Custom allauth adapters for suppressing toasts, handling exec codes on signup, and overriding error/cancellation pages
- **Email notifications** — Event subscription model and email dispatch for RSVPs
- **Ads feature** — `ClubAd`/`AdBooking` models, weekly scheduling grid with per-slot locking, and ad display on profile, forum, and messages pages
- **Documents feature** — `ClubDocument` model, executive file upload/delete, and the Documents tab
- **Bug fixes and deployment** — Migration conflict resolution, timezone fixes, responsive layout adjustments, and Heroku deployment troubleshooting

During the development process, we accounted for potential errors while using AI as a tool. We ensured that changes assisted with AI were thoroughly reviewed and implementations met requirements to ensure a quality final product.