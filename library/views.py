from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import Book, Borrow

User = get_user_model()

# --- Role Check Helper Functions ---
def is_admin(user):
    return user.is_authenticated and (user.role == User.ADMIN or user.is_superuser)

def is_librarian(user):
    return user.is_authenticated and user.role == User.LIBRARIAN

def is_librarian_or_admin(user):
    return user.is_authenticated and (
        user.role == User.LIBRARIAN or 
        user.role == User.ADMIN or 
        user.is_superuser  # ✅ superuser ও access পাবে
    )

# ── Auth Views ──

@login_required
def home(request):
    total_books = Book.objects.count()
    total_members = User.objects.filter(role=User.REGULAR_USER).count()
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
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        uname = request.POST.get('username')
        uemail = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        
        if pass1 != pass2:
            error = "Passwords do not match!"
        elif User.objects.filter(username=uname).exists():
            error = "Username already taken!"
        else:
            user = User.objects.create_user(
                username=uname,
                email=uemail,
                password=pass1,
                first_name=fname,
                last_name=lname,
                role=User.REGULAR_USER
            )
            return redirect('login')
    return render(request, 'library/register.html', {'error': error})

# ── Book Views ──

@login_required
def book_list(request):
    books = Book.objects.all()
    return render(request, 'library/book_list.html', {'books': books})

@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
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
@user_passes_test(is_librarian_or_admin, login_url='/')
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.title = request.POST['title']
        book.author = request.POST['author']
        book.isbn = request.POST['isbn']
        old_total = book.total_copies
        new_total = int(request.POST['total_copies'])
        diff = new_total - old_total
        book.total_copies = new_total
        book.available_copies += diff
        book.save()
        return redirect('book_list')
    return render(request, 'library/book_form.html', {'action': 'Edit', 'book': book})

@login_required
@user_passes_test(is_admin, login_url='/')
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    return redirect('book_list')

# ── Member Views ──

@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def member_list(request):
    members = User.objects.all().order_by('-date_joined')
    return render(request, 'library/member_list.html', {'members': members})

@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def member_add(request):
    error = ''
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST.get('role', User.REGULAR_USER)
        if User.objects.filter(username=username).exists():
            error = 'This username already exists!'
        else:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role
            )
            return redirect('member_list')
    return render(request, 'library/member_form.html', {'action': 'Add', 'error': error, 'roles': User.ROLE_CHOICES})

@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def member_edit(request, pk):
    member = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        member.username = request.POST['username']
        member.email = request.POST['email']
        if request.user.role == User.ADMIN or request.user.is_superuser:
            member.role = request.POST.get('role', member.role)
        member.save()
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
    return redirect('member_list')

# ── Borrow Views ──

@login_required
def borrow_list(request):
    if is_librarian_or_admin(request.user):
        # admin/librarian সব borrow দেখবে
        borrows = Borrow.objects.filter(is_returned=False)
    else:
        # regular user শুধু নিজের borrow দেখবে
        borrows = Borrow.objects.filter(member=request.user, is_returned=False)
    return render(request, 'library/borrow_list.html', {'borrows': borrows})

@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
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
    members = User.objects.filter(role=User.REGULAR_USER)
    return render(request, 'library/borrow_form.html', {'books': books, 'members': members})

@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def return_book(request, pk):
    borrow = get_object_or_404(Borrow, pk=pk)
    if not borrow.is_returned:
        borrow.is_returned = True
        borrow.return_date = timezone.now().date()
        borrow.save()
        borrow.book.available_copies += 1
        borrow.book.save()
    return redirect('borrow_list')

# ── Extra Pages ──

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
    borrows = Borrow.objects.filter(member=request.user, is_returned=False)
    return render(request, 'library/online_payment.html', {'borrows': borrows})

@login_required
def fines_dues(request):
    borrows = Borrow.objects.filter(member=request.user)
    fines = []
    for b in borrows:
        if not b.is_returned:
            days = (timezone.now().date() - b.borrow_date).days
            overdue = max(0, days - 14)  # 14 দিন free
            fine = overdue * 5           # প্রতিদিন ৫ টাকা
            if fine > 0:
                fines.append({'borrow': b, 'days_overdue': overdue, 'fine': fine})
    return render(request, 'library/fines_dues.html', {'fines': fines})

@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def system_monitoring(request):
    total_books = Book.objects.count()
    total_members = User.objects.filter(role=User.REGULAR_USER).count()
    active_borrows = Borrow.objects.filter(is_returned=False).count()
    returned_borrows = Borrow.objects.filter(is_returned=True).count()
    return render(request, 'library/system_monitoring.html', {
        'total_books': total_books,
        'total_members': total_members,
        'active_borrows': active_borrows,
        'returned_borrows': returned_borrows,
    })

@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def reports_analytics(request):
    books = Book.objects.all()
    recent_borrows = Borrow.objects.order_by('-borrow_date')[:10]
    return render(request, 'library/reports_analytics.html', {
        'books': books,
        'recent_borrows': recent_borrows,
    })