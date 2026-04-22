from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone

from .models import Book, Borrow, Member
from .forms import (
    BookForm,
    UserRegistrationForm,
    UserProfileForm,
    MemberProfileForm,
    BorrowForm,
    ReturnBookForm,
    PasswordChangeForm,
)

User = get_user_model()


# ===============================================
# ROLE CHECK
# ===============================================
def is_admin(user):
    return user.is_authenticated and (user.role == User.ADMIN or user.is_superuser)


def is_librarian(user):
    return user.is_authenticated and user.role == User.LIBRARIAN


def is_librarian_or_admin(user):
    return user.is_authenticated and (
        user.role in [User.LIBRARIAN, User.ADMIN] or user.is_superuser
    )


# ===============================================
# HOME / DASHBOARD
# ===============================================
@login_required
def home(request):
    return render(request, 'library/home.html', {
        'total_books': Book.objects.count(),
        'total_members': User.objects.filter(role=User.REGULAR_USER).count(),
        'total_borrows': Borrow.objects.filter(is_returned=False).count(),
    })


# ===============================================
# AUTH — LOGIN / LOGOUT / REGISTER
# ===============================================
def login_view(request):
    error = ''
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user:
            login(request, user)
            return redirect('home')
        error = "Invalid username or password!"
    return render(request, 'library/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    error = ''
    if request.method == 'POST':
        if request.POST.get('password1') != request.POST.get('password2'):
            error = "Passwords do not match!"
        elif User.objects.filter(username=request.POST.get('username')).exists():
            error = "Username already exists!"
        else:
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password1'),
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
                phone=request.POST.get('phone', ''),
                role=User.REGULAR_USER,
            )
            # ✅ Register করার সাথে সাথে Member profile তৈরি
            Member.objects.get_or_create(user=user)
            return redirect('login')

    return render(request, 'library/register.html', {'error': error})


# ===============================================
# USER PROFILE — manage name, email, contact
# ===============================================
@login_required
def manage_profile(request):
    # ✅ Member profile না থাকলে তৈরি করো
    member, created = Member.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        member_form = MemberProfileForm(
            request.POST,
            instance=member
        )

        if user_form.is_valid() and member_form.is_valid():
            user_form.save()
            member_form.save()
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('manage_profile')
        else:
            messages.error(request, '❌ Please fix the errors below.')
    else:
        user_form = UserProfileForm(instance=request.user)
        member_form = MemberProfileForm(instance=member)

    return render(request, 'library/manage_profile.html', {
        'user_form': user_form,
        'member_form': member_form,
    })


# ✅ Password Change
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            # পুরনো password check
            if not request.user.check_password(form.cleaned_data['old_password']):
                messages.error(request, '❌ Current password is incorrect!')
            else:
                request.user.set_password(form.cleaned_data['new_password1'])
                request.user.save()
                # ✅ Session ঠিক রাখো logout না হওয়ার জন্য
                update_session_auth_hash(request, request.user)
                messages.success(request, '✅ Password changed successfully!')
                return redirect('manage_profile')
    else:
        form = PasswordChangeForm()

    return render(request, 'library/change_password.html', {'form': form})


# ===============================================
# BOOKS
# ===============================================
@login_required
def book_list(request):
    books = Book.objects.all()
    query = request.GET.get('q', '')
    if query:
        books = books.filter(
            title__icontains=query
        ) | books.filter(
            author__icontains=query
        ) | books.filter(
            isbn__icontains=query
        )
    return render(request, 'library/book_list.html', {
        'books': books,
        'query': query
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def book_add(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.available_copies = book.total_copies
            book.save()
            messages.success(request, '✅ Book added successfully!')
            return redirect('book_list')
    else:
        form = BookForm()

    return render(request, 'library/book_form.html', {
        'form': form,
        'action': 'Add'
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == "POST":
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Book updated successfully!')
            return redirect('book_list')
    else:
        form = BookForm(instance=book)

    return render(request, 'library/book_form.html', {
        'form': form,
        'action': 'Edit'
    })


@login_required
@user_passes_test(is_admin, login_url='/')
def book_delete(request, pk):
    get_object_or_404(Book, pk=pk).delete()
    messages.success(request, '✅ Book deleted successfully!')
    return redirect('book_list')


# ===============================================
# MEMBERS
# ===============================================
@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def member_list(request):
    return render(request, 'library/member_list.html', {
        'members': User.objects.all().order_by('-date_joined')
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def member_add(request):
    error = ''
    if request.method == 'POST':
        if User.objects.filter(username=request.POST.get('username')).exists():
            error = 'Username already exists!'
        else:
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password'),
                phone=request.POST.get('phone', ''),
                role=request.POST.get('role', User.REGULAR_USER),
            )
            # ✅ Member profile তৈরি
            Member.objects.get_or_create(user=user)
            messages.success(request, '✅ Member added successfully!')
            return redirect('member_list')

    return render(request, 'library/member_form.html', {
        'action': 'Add',
        'error': error,
        'roles': User.ROLE_CHOICES
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def member_edit(request, pk):
    member = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        member.first_name = request.POST.get('first_name', member.first_name)
        member.last_name = request.POST.get('last_name', member.last_name)
        member.username = request.POST.get('username', member.username)
        member.email = request.POST.get('email', member.email)
        member.phone = request.POST.get('phone', member.phone)

        if request.user.role == User.ADMIN or request.user.is_superuser:
            member.role = request.POST.get('role', member.role)

        member.save()
        messages.success(request, '✅ Member updated successfully!')
        return redirect('member_list')

    return render(request, 'library/member_form.html', {
        'action': 'Edit',
        'member': member,
        'roles': User.ROLE_CHOICES
    })


@login_required
@user_passes_test(is_admin, login_url='/')
def member_delete(request, pk):
    member = get_object_or_404(User, pk=pk)
    if member != request.user:
        member.delete()
        messages.success(request, '✅ Member deleted successfully!')
    return redirect('member_list')


# ===============================================
# BORROW & RETURN
# ===============================================
@login_required
def borrow_list(request):
    if is_librarian_or_admin(request.user):
        borrows = Borrow.objects.filter(is_returned=False).select_related('book', 'member')
    else:
        borrows = Borrow.objects.filter(
            member=request.user
        ).select_related('book', 'member')

    return render(request, 'library/borrow_list.html', {'borrows': borrows})


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def borrow_book(request):
    if request.method == "POST":
        book = get_object_or_404(Book, pk=request.POST.get('book'))
        member = get_object_or_404(User, pk=request.POST.get('member'))

        if book.available_copies > 0:
            Borrow.objects.create(
                book=book,
                member=member,
                due_date=request.POST.get('due_date') or None
            )
            book.available_copies -= 1
            book.save()
            messages.success(request, f'✅ "{book.title}" borrowed by {member.username}!')
        else:
            messages.error(request, '❌ No copies available!')

        return redirect('borrow_list')

    return render(request, 'library/borrow_form.html', {
        'books': Book.objects.filter(available_copies__gt=0),
        'members': User.objects.filter(role=User.REGULAR_USER)
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def return_book(request, pk):
    borrow = get_object_or_404(Borrow, pk=pk)

    if not borrow.is_returned:
        borrow.is_returned = True
        borrow.return_date = timezone.now().date()
        borrow.status = 'returned'
        borrow.save()

        borrow.book.available_copies += 1
        borrow.book.save()
        messages.success(request, f'✅ "{borrow.book.title}" returned successfully!')

    return redirect('borrow_list')


# ===============================================
# EXTRA PAGES
# ===============================================
@login_required
def digital_resources(request):
    return render(request, 'library/digital_resources.html')


@login_required
def research_papers(request):
    return render(request, 'library/research_papers.html')


@login_required
def premium_content(request):
    return render(request, 'library/premium_content.html')


@login_required
def online_payment(request):
    return render(request, 'library/online_payment.html', {
        'borrows': Borrow.objects.filter(
            member=request.user,
            is_returned=False
        ).select_related('book')
    })


@login_required
def fines_dues(request):
    fines = []
    for b in Borrow.objects.filter(member=request.user).select_related('book'):
        if not b.is_returned:
            overdue = max(0, (timezone.now().date() - b.borrow_date).days - 14)
            if overdue > 0:
                fines.append({
                    'borrow': b,
                    'days_overdue': overdue,
                    'fine': overdue * 5
                })

    return render(request, 'library/fines_dues.html', {'fines': fines})


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def system_monitoring(request):
    return render(request, 'library/system_monitoring.html', {
        'total_books': Book.objects.count(),
        'total_members': User.objects.filter(role=User.REGULAR_USER).count(),
        'active_borrows': Borrow.objects.filter(is_returned=False).count(),
        'returned_borrows': Borrow.objects.filter(is_returned=True).count(),
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def reports_analytics(request):
    return render(request, 'library/reports_analytics.html', {
        'books': Book.objects.all(),
        'recent_borrows': Borrow.objects.order_by('-borrow_date').select_related('book', 'member')[:10],
    })