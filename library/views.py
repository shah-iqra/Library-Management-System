from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import FileResponse, HttpResponseForbidden

from .models import Book, Borrow, Member, ResearchPaper, Category, DigitalResource
from .forms import (
    BookForm,
    UserProfileForm,
    MemberProfileForm,
    BorrowForm,
    PasswordChangeForm,
    ResearchPaperForm,
    DigitalResourceForm,
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
# AUTH
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
            Member.objects.get_or_create(user=user)
            return redirect('login')

    return render(request, 'library/register.html', {'error': error})


# ===============================================
# PROFILE
# ===============================================
@login_required
def manage_profile(request):
    member, created = Member.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        member_form = MemberProfileForm(request.POST, instance=member)

        if user_form.is_valid() and member_form.is_valid():
            user_form.save()
            member_form.save()
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('manage_profile')
        messages.error(request, '❌ Please fix the errors below.')
    else:
        user_form = UserProfileForm(instance=request.user)
        member_form = MemberProfileForm(instance=member)

    return render(request, 'library/manage_profile.html', {
        'user_form': user_form,
        'member_form': member_form,
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            if not request.user.check_password(form.cleaned_data['old_password']):
                messages.error(request, '❌ Current password is incorrect!')
            else:
                request.user.set_password(form.cleaned_data['new_password1'])
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, '✅ Password changed successfully!')
                return redirect('manage_profile')
    else:
        form = PasswordChangeForm()

    return render(request, 'library/change_password.html', {'form': form})


# ===============================================
# CATEGORY MANAGEMENT
# ===============================================
@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'library/category_list.html', {'categories': categories})


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            if Category.objects.filter(name__iexact=name).exists():
                messages.error(request, '❌ Category already exists!')
            else:
                Category.objects.create(name=name)
                messages.success(request, '✅ Category added successfully!')
                return redirect('category_list')
        else:
            messages.error(request, '❌ Category name is required.')

    return render(request, 'library/category_form.html', {'action': 'Add'})


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            existing = Category.objects.filter(name__iexact=name).exclude(pk=category.pk)
            if existing.exists():
                messages.error(request, '❌ Another category with this name already exists!')
            else:
                category.name = name
                category.save()
                messages.success(request, '✅ Category updated successfully!')
                return redirect('category_list')
        else:
            messages.error(request, '❌ Category name is required.')

    return render(request, 'library/category_form.html', {
        'action': 'Edit',
        'category': category
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, '✅ Category deleted successfully!')
    return redirect('category_list')


# ===============================================
# BOOKS
# ===============================================
@login_required
def book_list(request):
    books = Book.objects.select_related('category').all().order_by('title')
    categories = Category.objects.all().order_by('name')

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    if query:
        books = books.filter(title__icontains=query) | books.filter(author__icontains=query) | books.filter(isbn__icontains=query)

    if category_id:
        books = books.filter(category_id=category_id)

    return render(request, 'library/book_list.html', {
        'books': books,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
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

    return render(request, 'library/book_form.html', {'form': form, 'action': 'Add'})


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == "POST":
        old_total = book.total_copies
        old_available = book.available_copies

        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            updated_book = form.save(commit=False)

            if updated_book.total_copies >= old_total:
                diff = updated_book.total_copies - old_total
                updated_book.available_copies = old_available + diff
            else:
                borrowed_count = old_total - old_available
                updated_book.available_copies = max(updated_book.total_copies - borrowed_count, 0)

            updated_book.save()
            messages.success(request, '✅ Book updated successfully!')
            return redirect('book_list')
    else:
        form = BookForm(instance=book)

    return render(request, 'library/book_form.html', {'form': form, 'action': 'Edit'})


@login_required
@user_passes_test(is_admin, login_url='/')
def book_delete(request, pk):
    get_object_or_404(Book, pk=pk).delete()
    messages.success(request, '✅ Book deleted successfully!')
    return redirect('book_list')


# ===============================================
# DIGITAL RESOURCES
# ===============================================
@login_required
def digital_resources(request):
    resources = DigitalResource.objects.select_related('uploaded_by').all().order_by('-uploaded_at')

    query = request.GET.get('q', '').strip()
    selected_type = request.GET.get('type', '').strip()

    if query:
        resources = resources.filter(title__icontains=query) | resources.filter(course_code__icontains=query)

    if selected_type:
        resources = resources.filter(resource_type=selected_type)

    return render(request, 'library/digital_resources.html', {
        'resources': resources,
        'query': query,
        'selected_type': selected_type,
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def digital_resource_add(request):
    if request.method == 'POST':
        form = DigitalResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, '✅ Digital resource added successfully!')
            return redirect('digital_resources')
    else:
        form = DigitalResourceForm()

    return render(request, 'library/resource_form.html', {
        'form': form,
        'action': 'Add'
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def digital_resource_edit(request, pk):
    resource = get_object_or_404(DigitalResource, pk=pk)

    if request.method == 'POST':
        form = DigitalResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Digital resource updated successfully!')
            return redirect('digital_resources')
    else:
        form = DigitalResourceForm(instance=resource)

    return render(request, 'library/resource_form.html', {
        'form': form,
        'action': 'Edit'
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def digital_resource_delete(request, pk):
    resource = get_object_or_404(DigitalResource, pk=pk)
    resource.delete()
    messages.success(request, '✅ Digital resource deleted successfully!')
    return redirect('digital_resources')


@login_required
def digital_resource_read(request, pk):
    resource = get_object_or_404(DigitalResource, pk=pk)
    return FileResponse(resource.file.open('rb'))


@login_required
def digital_resource_download(request, pk):
    resource = get_object_or_404(DigitalResource, pk=pk)
    return FileResponse(resource.file.open('rb'), as_attachment=True)


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
        borrows = Borrow.objects.filter(member=request.user).select_related('book', 'member')

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
def research_papers(request):
    papers = ResearchPaper.objects.filter(status='approved').order_by('-uploaded_at')
    query = request.GET.get('q', '')
    if query:
        papers = papers.filter(title__icontains=query) | papers.filter(author__icontains=query) | papers.filter(journal__icontains=query)
    return render(request, 'library/research_papers.html', {
        'papers': papers,
        'query': query,
        'is_librarian_or_admin': is_librarian_or_admin(request.user),
    })


@login_required
def premium_content(request):
    return render(request, 'library/premium_content.html')


@login_required
def online_payment(request):
    return render(request, 'library/online_payment.html', {
        'borrows': Borrow.objects.filter(member=request.user, is_returned=False).select_related('book')
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


# ===============================================
# RESEARCH PAPERS
# ===============================================
@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def manage_research_papers(request):
    papers = ResearchPaper.objects.all().order_by('-uploaded_at')
    return render(request, 'library/manage_research_papers.html', {'papers': papers})


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def upload_research_paper(request):
    if request.method == 'POST':
        form = ResearchPaperForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save(commit=False)
            paper.uploaded_by = request.user
            paper.status = 'pending'
            paper.save()
            return redirect('manage_research_papers')
    else:
        form = ResearchPaperForm()
    return render(request, 'library/upload_research_paper.html', {'form': form})


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def approval_access_control(request):
    pending_papers = ResearchPaper.objects.filter(status='pending').order_by('-uploaded_at')
    approved_papers = ResearchPaper.objects.filter(status='approved').order_by('-uploaded_at')
    rejected_papers = ResearchPaper.objects.filter(status='rejected').order_by('-uploaded_at')

    return render(request, 'library/approval_access_control.html', {
        'pending_papers': pending_papers,
        'approved_papers': approved_papers,
        'rejected_papers': rejected_papers,
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def approve_paper(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id)
    paper.status = 'approved'
    paper.save()
    return redirect('approval_access_control')


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def reject_paper(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id)
    paper.status = 'rejected'
    paper.save()
    return redirect('approval_access_control')


def approved_paper_list(request):
    papers = ResearchPaper.objects.filter(status='approved').order_by('-uploaded_at')
    return render(request, 'library/approved_paper_list.html', {'papers': papers})


def paper_detail(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id, status='approved')
    return render(request, 'library/paper_detail.html', {'paper': paper})


@login_required
def read_paper(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id)
    if paper.status != 'approved':
        return HttpResponseForbidden("This paper is not approved yet.")
    return FileResponse(paper.paper_file.open('rb'), content_type='application/pdf')


@login_required
def download_paper(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id)
    if paper.status != 'approved':
        return HttpResponseForbidden("This paper is not approved yet.")
    return FileResponse(paper.paper_file.open('rb'), as_attachment=True)