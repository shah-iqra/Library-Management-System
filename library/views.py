from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from datetime import date, datetime, timedelta
from django.contrib import messages
from django.utils import timezone
from django.http import FileResponse, HttpResponseForbidden, HttpResponse
import csv
import uuid
from django.db.models import Count
from .models import Borrow, ResearchPaper, Notification
from .models import Book, Wishlist
from .models import SupportTicket
from django.http import JsonResponse

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
    Payment,
    SystemLog,
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
    PaymentForm,
)

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

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
    user = request.user
    today = date.today()

    # Common stats for all roles
    total_books = Book.objects.count()
    total_members = User.objects.filter(role=User.REGULAR_USER).count()
    active_borrows = Borrow.objects.filter(is_returned=False).count()
    overdue_books = Borrow.objects.filter(
        is_returned=False,
        due_date__lt=today
    ).count()

    # Collection Summary by category
    category_data = (
        Book.objects
        .values('category__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    total_book_count = total_books if total_books > 0 else 1
    collection_summary = [
        {
            'name': item['category__name'] or 'Uncategorized',
            'count': item['count'],
            'percent': round(item['count'] / total_book_count * 100),
        }
        for item in category_data
    ]

    # Recent Activity (last 5 system logs)
    recent_logs = SystemLog.objects.select_related('user').order_by('-timestamp')[:5]

    # Role-specific data
    context = {
        'total_books': total_books,
        'total_members': total_members,
        'active_borrows': active_borrows,
        'overdue_books': overdue_books,
        'collection_summary': collection_summary,
        'recent_logs': recent_logs,
    }

    if user.role == User.ADMIN or user.is_superuser:
        context.update({
            'total_fines': sum(
                b.fine_amount
                for b in Borrow.objects.filter(fine_amount__gt=0)
            ),
            'total_payments': Payment.objects.count(),
            'pending_papers': ResearchPaper.objects.filter(status='pending').count(),
            'total_premium': PremiumContent.objects.filter(is_active=True).count(),
            'recent_borrows': Borrow.objects.select_related('book', 'member')
                .order_by('-borrow_date')[:5],
        })
        return render(request, 'library/home.html', context)

    elif user.role == User.LIBRARIAN:
        context.update({
            'pending_papers': ResearchPaper.objects.filter(status='pending').count(),
            'recent_borrows': Borrow.objects.select_related('book', 'member')
                .order_by('-borrow_date')[:5],
            'overdue_borrows': Borrow.objects.filter(
                is_returned=False, due_date__lt=today
            ).select_related('book', 'member')[:5],
        })
        return render(request, 'library/home.html', context)

    else:
        # Regular User — only their own data
        my_borrows = Borrow.objects.filter(member=user, is_returned=False)
        my_overdue = my_borrows.filter(due_date__lt=today).count()
        my_total_borrow = Borrow.objects.filter(member=user).count()
        my_fine = sum(b.fine_amount for b in my_borrows if b.fine_amount)

        context.update({
            'my_active_borrows': my_borrows.count(),
            'my_overdue': my_overdue,
            'my_total_borrow': my_total_borrow,
            'my_fine': my_fine,
            'my_borrow_list': my_borrows.select_related('book').order_by('-borrow_date')[:5],
        })
        return render(request, 'library/home.html', context)


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
            SystemLog.objects.create(
                user=user,
                action="Logged In",
                ip_address=request.META.get('REMOTE_ADDR')
            )
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
            SystemLog.objects.create(
                user=request.user,
                action="Added a Book",
                ip_address=request.META.get('REMOTE_ADDR')
            )
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

    Notification.objects.create(
        user=request.user,
        message=f"✅ You have borrowed '{book.title}'. Due date: {due_date}"
    )

    book.available_copies -= 1
    book.save()

    messages.success(request, f'✅ "{book.title}" borrowed successfully! Due date: {due_date}')
    return redirect('borrow_list')


@login_required
def borrow_list(request):
    borrows = Borrow.objects.select_related(
        'book',
        'member'
    ).order_by('-borrow_date')

    if request.user.role == User.REGULAR_USER:
        borrows = borrows.filter(member=request.user)

    today = timezone.now().date()

    for borrow in borrows:
        if not borrow.is_returned and borrow.due_date:
            overdue_days = (today - borrow.due_date).days
            if overdue_days > 0:
                borrow.status = 'overdue'
                borrow.fine_amount = overdue_days * 5
                borrow.save()
            else:
                borrow.fine_amount = 0
                borrow.save()

    return render(request, 'library/borrow_list.html', {
        'borrows': borrows,
        'today': today,
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

        Notification.objects.create(
            user=member,
            message=f"📚 '{book.title}' has been issued to you. Due date: {due_date}"
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

    Notification.objects.create(
        user=borrow.member,
        message=f"🔄 '{borrow.book.title}' has been returned successfully."
    )

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
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        username = email if email else name.lower().replace(' ', '_')

        if not username:
            error = '❌ Name or Email is required!'
        elif User.objects.filter(username=username).exists():
            error = '❌ A member with this email already exists!'
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=uuid.uuid4().hex,
                first_name=name,
                phone=phone,
                role=User.REGULAR_USER,
            )
            Member.objects.get_or_create(user=user)
            messages.success(request, '✅ Member added successfully!')
            return redirect('member_list')

    return render(request, 'library/member_form.html', {
        'action': 'Add',
        'error': error,
        'roles': User.ROLE_CHOICES,
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
    year = request.GET.get('year', '').strip()
    if query:
        papers = papers.filter(title__icontains=query) | papers.filter(author__icontains=query) | papers.filter(journal__icontains=query)
    if year:
        papers = papers.filter(year=year)
    return render(request, 'library/research_papers.html', {
        'papers': papers,
        'query': query,
        'is_librarian_or_admin': is_librarian_or_admin(request.user),
    })


# ==================================================
# PAYMENT SYSTEM
# ==================================================

@login_required
def online_payment(request):
    borrow_id = request.GET.get('borrow_id')
    borrow = None
    prefill_amount = 0

    if borrow_id:
        borrow = get_object_or_404(Borrow, id=borrow_id)
        prefill_amount = borrow.fine_amount if borrow.fine_amount > 0 else 50

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.status = 'Success'
            payment.save()

            Notification.objects.create(
                user=request.user,
                message=f"💳 Payment of ৳{payment.amount} was successful. Transaction ID: {payment.transaction_id}"
            )

            if borrow and borrow.fine_amount > 0:
                borrow.fine_amount = 0
                borrow.save()

            messages.success(request, '✅ Payment successful!')
            return redirect('payment_history')
    else:
        form = PaymentForm(initial={'amount': prefill_amount})

    return render(request, 'library/online_payment.html', {
        'form': form,
        'borrow': borrow,
        'prefill_amount': prefill_amount,
    })


@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-payment_date')
    return render(request, 'library/payment_history.html', {'payments': payments})


@login_required
def download_payment_history_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="payment_history.pdf"'
    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=20
    )
    elements = []
    styles = getSampleStyleSheet()
    title = Paragraph(
        "<font size=22><b>Library Payment History</b></font>",
        styles['Title']
    )
    elements.append(title)
    elements.append(Spacer(1, 20))
    user_info = Paragraph(
        f"""
        <b>User:</b> {request.user.username}<br/>
        <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
        """,
        styles['Normal']
    )
    elements.append(user_info)
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%"))
    elements.append(Spacer(1, 15))
    payments = Payment.objects.filter(user=request.user).order_by('-payment_date')
    data = [['Date', 'Method', 'Amount', 'Transaction ID', 'Status']]
    for payment in payments:
        data.append([
            payment.payment_date.strftime("%Y-%m-%d"),
            payment.method,
            f"TK{payment.amount}",
            payment.transaction_id,
            payment.status
        ])
    table = Table(data, colWidths=[100, 90, 80, 140, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1cc78")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 30))
    footer = Paragraph(
        "<font size=10 color='grey'>Generated by Library Management System</font>",
        styles['Normal']
    )
    elements.append(footer)
    doc.build(elements)
    return response


@login_required
def fines_dues(request):
    borrows = Borrow.objects.filter(is_returned=False)

    for borrow in borrows:
        if borrow.due_date and date.today() > borrow.due_date:
            overdue_days = (date.today() - borrow.due_date).days
            borrow.fine_amount = overdue_days * 5
        else:
            borrow.fine_amount = 0

    context = {
        'borrows': borrows,
        'today': date.today(),
    }

    return render(request, 'library/fines_dues.html', context)


# ==================================================
# SYSTEM MONITORING
# ==================================================

@login_required
@user_passes_test(is_librarian_or_admin, login_url='/')
def system_monitoring(request):
    logs = SystemLog.objects.all().order_by('-timestamp')[:20]
    total_logs = SystemLog.objects.count()
    context = {
        'logs': logs,
        'total_logs': total_logs,
        'total_books': Book.objects.count(),
        'total_members': User.objects.filter(role=User.REGULAR_USER).count(),
        'active_borrows': Borrow.objects.filter(is_returned=False).count(),
        'returned_borrows': Borrow.objects.filter(is_returned=True).count(),
    }
    return render(request, 'library/system_monitoring.html', context)


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
            SystemLog.objects.create(
                user=request.user,
                action="Uploaded Research Paper",
                ip_address=request.META.get('REMOTE_ADDR')
            )
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
            transaction_id = form.cleaned_data['transaction_id'].strip()

            if PremiumPurchase.objects.filter(transaction_id=transaction_id).exists():
                messages.error(request, '❌ This Transaction ID has already been used! Please enter a valid one.')
                return render(request, 'library/purchase_premium.html', {
                    'content': content,
                    'form': form
                })

            PremiumPurchase.objects.create(
                user=request.user,
                content=content,
                amount_paid=content.price,
                transaction_id=transaction_id
            )
            messages.success(request, "✅ Purchase successful! You now have access.")
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

    video_url = content.video_url
    if video_url:
        if 'watch?v=' in video_url:
            video_id = video_url.split('watch?v=')[-1].split('&')[0]
            video_url = f'https://www.youtube-nocookie.com/embed/{video_id}'
        elif 'youtu.be/' in video_url:
            video_id = video_url.split('youtu.be/')[-1].split('?')[0]
            video_url = f'https://www.youtube-nocookie.com/embed/{video_id}'
        elif 'embed/' in video_url:
            video_url = 'https://www.youtube-nocookie.com/embed/' + video_url.split('embed/')[-1].split('?')[0]

    return render(request, 'library/view_premium_content.html', {
        'content': content,
        'video_url': video_url,
    })


@login_required
def admin_upload_premium(request):
    if request.method == 'POST':
        form = PremiumContentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Content uploaded successfully!')
            return redirect('premium_content')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'❌ {field}: {error}')
    else:
        form = PremiumContentForm()
    return render(request, 'library/admin_upload_premium.html', {'form': form})


@login_required
def premium_content(request):
    contents = PremiumContent.objects.filter(is_active=True).order_by('-id')
    purchased_ids = PremiumPurchase.objects.filter(
        user=request.user
    ).values_list('content_id', flat=True)

    return render(request, 'library/premium_content.html', {
        'contents': contents,
        'purchased_ids': list(purchased_ids),
    })


@login_required
def admin_premium_purchases(request):
    if not request.user.is_staff:
        return redirect('home')
    purchases = PremiumPurchase.objects.all().select_related('user', 'content')
    return render(request, 'library/admin_premium_purchases.html', {'purchases': purchases})


@login_required
def premium_content_delete(request, pk):
    if not (request.user.is_staff or request.user.role == 'admin'):
        messages.error(request, '❌ Permission denied!')
        return redirect('premium_content')

    content = get_object_or_404(PremiumContent, pk=pk)
    content.file.delete(save=False)
    content.delete()
    messages.success(request, '✅ Content deleted successfully!')
    return redirect('premium_content')


def export_members_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="member_list.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'Phone', 'Date Joined'])

    members = User.objects.all()
    for member in members:
        writer.writerow([member.id, member.username, member.email, getattr(member, 'phone', 'N/A'), member.date_joined])

    return response


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(BookReview, id=review_id)

    if request.user == review.user or request.user.role == 'admin':
        review.delete()
        messages.success(request, "Review deleted successfully!")
    else:
        messages.error(request, "You are not allowed to delete this review.")

    return redirect('book_detail', pk=review.book.id)


@login_required
def dashboard(request):
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'library/home.html')


@login_required
def notification_page(request):
    user = request.user

    # Overdue notification
    overdue_books = Borrow.objects.filter(
        member=user,
        due_date__lt=date.today(),
        is_returned=False
    )
    for borrow in overdue_books:
        msg = f"⚠️ '{borrow.book.title}' is overdue! Fine: {borrow.fine_amount} Tk"
        already_exists = Notification.objects.filter(
            user=user,
            message__contains=borrow.book.title
        ).exists()
        if not already_exists:
            Notification.objects.create(user=user, message=msg)

    # Admin/Librarian — pending paper notification
    if user.role in ['admin', 'librarian']:
        pending_papers = ResearchPaper.objects.filter(status='pending')
        for paper in pending_papers:
            if not Notification.objects.filter(
                user=user,
                message__contains=paper.title
            ).exists():
                Notification.objects.create(
                    user=user,
                    message=f"📄 '{paper.title}' paper is pending approval."
                )

    notifications = Notification.objects.filter(
        user=user
    ).order_by('-created_at')

    Notification.objects.filter(
        user=user,
        is_read=False
    ).update(is_read=True)

    return render(request, 'library/notifications.html', {
        'notifications': notifications
    })


@login_required
def wishlist_page(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).order_by('-added_at')
    return render(request, 'library/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def add_to_wishlist(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    Wishlist.objects.get_or_create(user=request.user, book=book)
    return redirect('wishlist_page')


@login_required
def remove_from_wishlist(request, wishlist_id):
    item = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    item.delete()
    return redirect('wishlist_page')


@login_required
def help_support_page(request):
    user = request.user

    if user.role.lower() in ['admin', 'librarian']:
        if request.method == 'POST':
            ticket_id = request.POST.get('ticket_id')
            admin_reply = request.POST.get('admin_reply')
            if ticket_id and admin_reply:
                ticket = get_object_or_404(SupportTicket, id=ticket_id)
                ticket.admin_reply = admin_reply
                ticket.status = 'resolved'
                ticket.save()

                Notification.objects.create(
                    user=ticket.user,
                    message=f"💬 Admin has replied to your '{ticket.subject}' ticket."
                )
                messages.success(request, f"Replied to {ticket.user.username}'s ticket successfully!")
                return redirect('help_support_page')

        all_tickets = SupportTicket.objects.all().order_by('status', '-created_at')
        return render(request, 'library/help_support.html', {'all_tickets': all_tickets})

    else:
        if request.method == 'POST':
            subject = request.POST.get('subject')
            message_text = request.POST.get('message')
            if subject and message_text:
                SupportTicket.objects.create(user=user, subject=subject, message=message_text)
                messages.success(request, "Your support ticket has been submitted successfully!")
                return redirect('help_support_page')

        my_tickets = SupportTicket.objects.filter(user=user).order_by('-created_at')
        return render(request, 'library/help_support.html', {'my_tickets': my_tickets})


def toggle_wishlist(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, book=book)

    if wishlist_item.exists():
        wishlist_item.delete()
        status = "removed"
    else:
        Wishlist.objects.create(user=request.user, book=book)
        status = "added"

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': status})

    return redirect(request.META.get('HTTP_REFERER', 'book_list'))


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'library/wishlist.html', {'wishlist_items': wishlist_items})