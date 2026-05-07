from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import FileResponse, HttpResponseForbidden, HttpResponse
from datetime import timedelta
import csv
import uuid

from .models import (
    Book,
    BookReview,
    Borrow,
    Member,
    ResearchPaper,
    Category,
    DigitalResource,
    PremiumContent,
    PremiumPurchase,
)

from .forms import (
    BookForm,
    BookReviewForm,
    UserProfileForm,
    MemberProfileForm,
    BorrowForm,
    PasswordChangeForm,
    ResearchPaperForm,
    DigitalResourceForm,
    PremiumContentForm,
    PremiumPurchaseForm,
)

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and (user.role == User.ADMIN or user.is_superuser)


def is_librarian(user):
    return user.is_authenticated and user.role == User.LIBRARIAN


def is_librarian_or_admin(user):
    return user.is_authenticated and (
        user.role in [User.LIBRARIAN, User.ADMIN] or user.is_superuser
    )


@login_required
def home(request):
    return render(request, 'library/home.html', {
        'total_books': Book.objects.count(),
        'total_members': User.objects.filter(role=User.REGULAR_USER).count(),
        'total_borrows': Borrow.objects.filter(is_returned=False).count(),
    })


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
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.select_related('user').all()
    user_review = BookReview.objects.filter(book=book, user=request.user).first()

    if request.method == "POST":
        form = BookReviewForm(request.POST, instance=user_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            review.save()
            messages.success(request, '✅ Review submitted successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookReviewForm(instance=user_review)

    active_borrow = Borrow.objects.filter(
        book=book,
        member=request.user,
        is_returned=False
    ).first()

    return render(request, 'library/book_detail.html', {
        'book': book,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
        'average_rating': book.average_rating(),
        'total_reviews': book.total_reviews(),
        'active_borrow': active_borrow,
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


# ==================================================
# BOOK BORROWING & RETURN SYSTEM
# ==================================================

@login_required
def issue_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if book.available_copies <= 0:
        messages.error(request, '❌ No copies available!')
        return redirect('book_detail', pk=book.id)

    already_borrowed = Borrow.objects.filter(
        book=book,
        member=request.user,
        is_returned=False
    ).exists()

    if already_borrowed:
        messages.error(request, '❌ You already borrowed this book.')
        return redirect('book_detail', pk=book.id)

    due_date = timezone.now().date() + timedelta(days=14)

    Borrow.objects.create(
        book=book,
        member=request.user,
        due_date=due_date,
        is_returned=False,
        status='borrowed'
    )

    book.available_copies -= 1
    book.save()

    messages.success(request, f'✅ "{book.title}" borrowed successfully! Due date: {due_date}')
    return redirect('borrow_list')


@login_required
def borrow_list(request):
    if is_librarian_or_admin(request.user):
        borrows = Borrow.objects.select_related('book', 'member').all().order_by('-borrow_date')
    else:
        borrows = Borrow.objects.filter(member=request.user).select_related('book', 'member').order_by('-borrow_date')

    return render(request, 'library/borrow_list.html', {
        'borrows': borrows,
        'today': timezone.now().date()
    })


@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def borrow_book(request):
    if request.method == "POST":
        book = get_object_or_404(Book, pk=request.POST.get('book'))
        member = get_object_or_404(User, pk=request.POST.get('member'))

        if book.available_copies <= 0:
            messages.error(request, '❌ No copies available!')
            return redirect('borrow_book')

        already_borrowed = Borrow.objects.filter(
            book=book,
            member=member,
            is_returned=False
        ).exists()

        if already_borrowed:
            messages.error(request, '❌ This member already borrowed this book.')
            return redirect('borrow_book')

        selected_due_date = request.POST.get('due_date')

        if selected_due_date:
            due_date = timezone.datetime.strptime(selected_due_date, "%Y-%m-%d").date()
        else:
            due_date = timezone.now().date() + timedelta(days=14)

        Borrow.objects.create(
            book=book,
            member=member,
            due_date=due_date,
            is_returned=False,
            status='borrowed',
            notes=request.POST.get('notes', '')
        )

        book.available_copies -= 1
        book.save()

        messages.success(request, f'✅ "{book.title}" borrowed by {member.username}!')
        return redirect('borrow_list')

    return render(request, 'library/borrow_form.html', {
        'books': Book.objects.filter(available_copies__gt=0),
        'members': User.objects.filter(role=User.REGULAR_USER)
    })

@login_required
def return_book(request, pk):
    borrow = get_object_or_404(Borrow, pk=pk)

    if not (is_librarian_or_admin(request.user) or borrow.member == request.user):
        return HttpResponseForbidden("You are not allowed to return this book.")

    if borrow.is_returned:
        messages.error(request, '❌ This book is already returned.')
        return redirect('borrow_list')

    borrow.is_returned = True
    borrow.return_date = timezone.now().date()
    borrow.status = 'returned'
    borrow.save()

    borrow.book.available_copies += 1
    borrow.book.save()

    messages.success(request, f'✅ "{borrow.book.title}" returned successfully!')
    return redirect('borrow_list')


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
def reports_analytics(request):
    download_type = request.GET.get('download')

    if download_type == 'borrow_report':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="borrow_activity_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['User', 'Book', 'Due Date', 'Status'])

        for b in Borrow.objects.all():
            writer.writerow([b.member.username, b.book.title, b.due_date, b.status])
        return response

    elif download_type == 'paper_report':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="research_papers_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Title', 'Author', 'Journal', 'Year'])

        for paper in ResearchPaper.objects.all():
            writer.writerow([paper.title, paper.author, paper.journal, paper.year])
        return response

    elif download_type == 'system_usage':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="system_usage_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Role', 'Date Joined'])

        for u in User.objects.all():
            writer.writerow([u.username, u.email, u.role, u.date_joined])
        return response

    total_borrows = Borrow.objects.count()
    total_papers = ResearchPaper.objects.count()
    total_users = User.objects.count()
    recent_activities = Borrow.objects.all().order_by('-id')[:4]

    return render(request, 'library/reports_analytics.html', {
        'total_borrows': total_borrows,
        'total_papers': total_papers,
        'total_users': total_users,
        'recent_activities': recent_activities,
    })


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


@login_required
def premium_content_list(request):
    contents = PremiumContent.objects.filter(is_active=True)
    purchased_ids = PremiumPurchase.objects.filter(
        user=request.user
    ).values_list('content_id', flat=True)

    return render(request, 'library/premium_content.html', {
        'contents': contents,
        'purchased_ids': purchased_ids,
    })


@login_required
def purchase_premium(request, pk):
    content = get_object_or_404(PremiumContent, pk=pk, is_active=True)

    if PremiumPurchase.objects.filter(user=request.user, content=content).exists():
        messages.info(request, "You already own this content!")
        return redirect('view_premium', pk=pk)

    if request.method == 'POST':
        form = PremiumPurchaseForm(request.POST)
        if form.is_valid():
            PremiumPurchase.objects.create(
                user=request.user,
                content=content,
                amount_paid=content.price,
                transaction_id=form.cleaned_data['transaction_id']
            )
            messages.success(request, "Purchase successful! You now have access.")
            return redirect('view_premium', pk=pk)
    else:
        form = PremiumPurchaseForm()

    return render(request, 'library/purchase_premium.html', {
        'content': content,
        'form': form
    })


@login_required
def view_premium_content(request, pk):
    content = get_object_or_404(PremiumContent, pk=pk)
    has_access = PremiumPurchase.objects.filter(
        user=request.user,
        content=content
    ).exists()

    if not has_access:
        messages.error(request, "Please purchase this content first.")
        return redirect('purchase_premium', pk=pk)

    return render(request, 'library/view_premium_content.html', {'content': content})


@login_required
def admin_upload_premium(request):
    if request.method == 'POST':
        form = PremiumContentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Content uploaded successfully!')
            return redirect('premium_content')
    else:
        form = PremiumContentForm()

    return render(request, 'library/admin_upload_premium.html', {'form': form})


@login_required
def admin_premium_purchases(request):
    if not request.user.is_staff:
        return redirect('home')

    purchases = PremiumPurchase.objects.all().select_related('user', 'content')
    return render(request, 'library/admin_premium_purchases.html', {'purchases': purchases})