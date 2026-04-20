from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Book, Borrow
from django.utils import timezone

User = get_user_model()

# --- Role Check Helper Functions ---
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_librarian(user):
    return user.is_authenticated and user.role == 'librarian'

def is_librarian_or_admin(user):
    return user.is_authenticated and (user.role == 'librarian' or user.role == 'admin')

# ── Auth Views ──

@login_required
def home(request):
    total_books = Book.objects.count()
    total_members = User.objects.filter(role='user').count()
    total_borrows = Borrow.objects.filter(is_returned=False).count()
    return render(request, 'library/home.html', {
        'total_books': total_books,
        'total_members': total_members,
        'total_borrows': total_borrows,
    })

def login_view(request):
    error = ''
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            error = 'Invalid username or password!'
    return render(request, 'library/login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    error = ''
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        role = request.POST.get('role', 'user')
        first_name = request.POST.get('first_name', '')  # ✅
        last_name = request.POST.get('last_name', '')    # ✅

        if password1 != password2:
            error = 'Passwords do not match!'
        elif User.objects.filter(username=username).exists():
            error = 'This username already exists!'
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                role=role,
                first_name=first_name,  # ✅
                last_name=last_name,    # ✅
            )
            login(request, user)
            return redirect('home')
    return render(request, 'library/register.html', {'error': error})

# ── Book Views ──

@login_required
def book_list(request):
    books = Book.objects.all()
    return render(request, 'library/book_list.html', {'books': books})

@login_required
@user_passes_test(is_librarian_or_admin)
def book_add(request):
    if request.method == 'POST':
        Book.objects.create(
            title=request.POST['title'],
            author=request.POST['author'],
            isbn=request.POST['isbn'],
            total_copies=request.POST['total_copies'],
            available_copies=request.POST['total_copies'],
        )
        return redirect('book_list')
    return render(request, 'library/book_form.html', {'action': 'Add'})

@login_required
@user_passes_test(is_librarian_or_admin)
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.title = request.POST['title']
        book.author = request.POST['author']
        book.isbn = request.POST['isbn']
        book.total_copies = int(request.POST['total_copies'])
        book.save()
        return redirect('book_list')
    return render(request, 'library/book_form.html', {'action': 'Edit', 'book': book})

@login_required
@user_passes_test(is_admin)
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    return redirect('book_list')

# ── Member Views ──

@login_required
@user_passes_test(is_librarian_or_admin)
def member_list(request):
    members = User.objects.filter(role='user')
    return render(request, 'library/member_list.html', {'members': members})

@login_required
@user_passes_test(is_librarian_or_admin)
def member_add(request):
    error = ''
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            error = 'This username already exists!'
        else:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='user'
            )
            return redirect('member_list')
    return render(request, 'library/member_form.html', {'action': 'Add', 'error': error})

@login_required
@user_passes_test(is_librarian_or_admin)
def member_edit(request, pk):
    member = get_object_or_404(User, pk=pk)
    error = ''
    if request.method == 'POST':
        member.username = request.POST['username']
        member.email = request.POST['email']
        member.save()
        return redirect('member_list')
    return render(request, 'library/member_form.html', {'action': 'Edit', 'member': member, 'error': error})

@login_required
@user_passes_test(is_admin)
def member_delete(request, pk):
    member = get_object_or_404(User, pk=pk)
    member.delete()
    return redirect('member_list')

# ── Borrow Views ──

@login_required
@user_passes_test(is_librarian_or_admin)
def borrow_list(request):
    borrows = Borrow.objects.filter(is_returned=False)
    return render(request, 'library/borrow_list.html', {'borrows': borrows})

@login_required
@user_passes_test(is_librarian_or_admin)
def borrow_book(request):
    if request.method == 'POST':
        book = get_object_or_404(Book, pk=request.POST['book'])
        member_user = get_object_or_404(User, pk=request.POST['member'])
        if book.available_copies > 0:
            Borrow.objects.create(book=book, member=member_user)
            book.available_copies -= 1
            book.save()
            return redirect('borrow_list')
    books = Book.objects.filter(available_copies__gt=0)
    members = User.objects.filter(role='user')
    return render(request, 'library/borrow_form.html', {'books': books, 'members': members})

@login_required
@user_passes_test(is_librarian_or_admin)
def return_book(request, pk):
    borrow = get_object_or_404(Borrow, pk=pk)
    if not borrow.is_returned:
        borrow.is_returned = True
        borrow.return_date = timezone.now().date()
        borrow.save()
        borrow.book.available_copies += 1
        borrow.book.save()
    return redirect('borrow_list')