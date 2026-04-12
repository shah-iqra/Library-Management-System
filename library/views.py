from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Book, Member, Borrow
from django.utils import timezone

# ── Auth Views ──
@login_required
def home(request):
    total_books = Book.objects.count()
    total_members = Member.objects.count()
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
            error = 'Username অথবা Password ভুল!'
    return render(request, 'library/login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')

# ── Book Views ──
@login_required
def book_list(request):
    books = Book.objects.all()
    return render(request, 'library/book_list.html', {'books': books})

@login_required
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
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.title = request.POST['title']
        book.author = request.POST['author']
        book.isbn = request.POST['isbn']
        book.total_copies = request.POST['total_copies']
        book.save()
        return redirect('book_list')
    return render(request, 'library/book_form.html', {'action': 'Edit', 'book': book})

@login_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    return redirect('book_list')

# ── Member Views ──
@login_required
def member_list(request):
    members = Member.objects.all()
    return render(request, 'library/member_list.html', {'members': members})

@login_required
def member_add(request):
    if request.method == 'POST':
        Member.objects.create(
            name=request.POST['name'],
            email=request.POST['email'],
            phone=request.POST['phone'],
        )
        return redirect('member_list')
    return render(request, 'library/member_form.html', {'action': 'Add'})

@login_required
def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        member.name = request.POST['name']
        member.email = request.POST['email']
        member.phone = request.POST['phone']
        member.save()
        return redirect('member_list')
    return render(request, 'library/member_form.html', {'action': 'Edit', 'member': member})

@login_required
def member_delete(request, pk):
    member = get_object_or_404(Member, pk=pk)
    member.delete()
    return redirect('member_list')

# ── Borrow Views ──
@login_required
def borrow_list(request):
    borrows = Borrow.objects.filter(is_returned=False)
    return render(request, 'library/borrow_list.html', {'borrows': borrows})

@login_required
def borrow_book(request):
    if request.method == 'POST':
        book = get_object_or_404(Book, pk=request.POST['book'])
        member = get_object_or_404(Member, pk=request.POST['member'])
        if book.available_copies > 0:
            Borrow.objects.create(book=book, member=member)
            book.available_copies -= 1
            book.save()
        return redirect('borrow_list')
    books = Book.objects.filter(available_copies__gt=0)
    members = Member.objects.all()
    return render(request, 'library/borrow_form.html', {'books': books, 'members': members})

@login_required
def return_book(request, pk):
    borrow = get_object_or_404(Borrow, pk=pk)
    borrow.is_returned = True
    borrow.return_date = timezone.now().date()
    borrow.save()
    borrow.book.available_copies += 1
    borrow.book.save()
    return redirect('borrow_list')