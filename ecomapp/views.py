from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, CartItem
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
# Admin Dashboard
@login_required
def admin_dashboard(request):
    products = Product.objects.all()
    return render(request, 'admin_dashboard.html', {'products': products})

# Add Product
@login_required
def add_product(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        image = request.FILES['image']
        category = request.POST.get('category', 'necklace')
        Product.objects.create(name=name, description=description, price=price, image=image, category=category)
        return redirect('admin_dashboard')
    return render(request, 'add_product.html')

# Edit Product
@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.description = request.POST['description']
        product.price = request.POST['price']
        product.category = request.POST.get('category', product.category)
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        return redirect('admin_dashboard')
    return render(request, 'edit_product.html', {'product': product})

# Delete Product
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('admin_dashboard')


from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import messages

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')

# def user_logout(request):
#     logout(request)
#     return redirect('login')


def userlogin(request):
    next_url = request.GET.get('next') or request.POST.get('next')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to the next URL if provided (from login_required), otherwise go to home
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            # Pass error and next URL back to template
            return render(request, 'userlogin.html', {
                'error': 'Invalid username or password. Please try again.',
                'next': next_url
            })
    # Pass next URL to template so it's preserved in the form
    return render(request, 'userlogin.html', {'next': next_url})


def user_logout(request):
    logout(request)
    return redirect('home')


def home(request):
    query = request.GET.get('q', '').strip()
    if query:
        products = Product.objects.filter(name__icontains=query)
        # Group by category for search results
        products_by_category = {}
        for product in products:
            if product.category not in products_by_category:
                products_by_category[product.category] = []
            products_by_category[product.category].append(product)
    else:
        # Group all products by category
        all_products = Product.objects.all()
        products_by_category = {
            'necklace': [],
            'earring': [],
            'bangle': [],
            'bracelet': [],
        }
        for product in all_products:
            if product.category in products_by_category:
                products_by_category[product.category].append(product)
    
    context = {
        'products_by_category': products_by_category,
        'q': query,
    }
    return render(request, 'home.html', context)

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            return render(request, 'register.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already taken'})

        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email already registered'})

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        return redirect('userlogin')

    return render(request, 'register.html')



from django.contrib.auth.decorators import login_required

@login_required(login_url='userlogin')
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    total_price = sum([item.total_price for item in cart_items])
    total_items = sum([item.quantity for item in cart_items])

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items
    }
    return render(request, 'cart.html', context)


@login_required(login_url='userlogin')
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('home')
    product = get_object_or_404(Product, id=product_id)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save()
    return redirect('cart')


@login_required(login_url='userlogin')
def update_cart_item(request, item_id):
    if request.method != 'POST':
        return redirect('cart')
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    action = request.POST.get('action')
    if action == 'inc':
        item.quantity += 1
        item.save()
    elif action == 'dec':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    elif action == 'remove':
        item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return updated totals and line subtotal for dynamic UI updates
        items = CartItem.objects.filter(user=request.user).select_related('product')
        total_price = sum([i.total_price for i in items])
        total_items = sum([i.quantity for i in items])
        line_total = 0
        quantity = 0
        if item_id and CartItem.objects.filter(id=item_id, user=request.user).exists():
            latest = CartItem.objects.get(id=item_id)
            line_total = float(latest.total_price)
            quantity = latest.quantity
        from django.http import JsonResponse
        return JsonResponse({
            'ok': True,
            'total_price': float(total_price),
            'total_items': total_items,
            'item_id': item_id,
            'line_total': line_total,
            'quantity': quantity,
            'removed': not CartItem.objects.filter(id=item_id, user=request.user).exists(),
        })
    return redirect('cart')


@login_required(login_url='userlogin')
def remove_cart_item(request, item_id):
    if request.method != 'POST':
        return redirect('cart')
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('cart')


@login_required(login_url='userlogin')
def checkout(request):
    if request.method != 'POST':
        return redirect('cart')

    # Get cart items before clearing
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    if not cart_items.exists():
        return redirect('cart')
    
    # Calculate totals
    total_price = sum([item.total_price for item in cart_items])
    total_items = sum([item.quantity for item in cart_items])
    
    # Store order information in session before clearing cart
    ts = timezone.now().strftime('%Y%m%d%H%M%S')
    order_id = f"INV-{request.user.id}-{ts}"
    request.session['last_order'] = {
        'order_id': order_id,
        'total_price': float(total_price),
        'total_items': total_items,
        'cart_items_data': [
            {
                'product_name': item.product.name,
                'product_price': float(item.product.price),
                'quantity': item.quantity,
                'line_total': float(item.total_price),
            }
            for item in cart_items
        ]
    }
    
    # Clear the cart after storing order data
    cart_items.delete()
    
    return redirect('invoice')


@login_required(login_url='userlogin')
def invoice(request):
    # Get order data from session (cart is cleared after checkout)
    order_meta = request.session.get('last_order', {})
    
    if not order_meta:
        # If no order data, redirect to cart
        return redirect('cart')
    
    # Create mock cart items from session data for template compatibility
    class MockCartItem:
        def __init__(self, item_data):
            self.product = type('Product', (), {
                'name': item_data['product_name'],
                'price': item_data['product_price']
            })()
            self.quantity = item_data['quantity']
            self.total_price = item_data['line_total']
    
    cart_items = [MockCartItem(item) for item in order_meta.get('cart_items_data', [])]
    total_price = order_meta.get('total_price', 0)
    total_items = order_meta.get('total_items', 0)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items,
        'order_id': order_meta.get('order_id'),
    }
    return render(request, 'invoice.html', context)


@login_required(login_url='userlogin')
def download_invoice(request):
    # Generate a simple PDF invoice using ReportLab
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except Exception:
        # Fallback: redirect to HTML invoice if ReportLab is not available
        return redirect('invoice')

    # Get order data from session (cart is cleared after checkout)
    order_meta = request.session.get('last_order', {})
    if not order_meta or not order_meta.get('cart_items_data'):
        return redirect('cart')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "InStyle Trends - Invoice")
    y -= 25
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Customer: {request.user.username}")
    y -= 15
    ts = timezone.now().strftime('%Y-%m-%d %H:%M')
    p.drawString(50, y, f"Date: {ts}")
    y -= 30

    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Product")
    p.drawString(320, y, "Price")
    p.drawString(400, y, "Qty")
    p.drawString(460, y, "Subtotal")
    y -= 12
    p.line(50, y, 545, y)
    y -= 16
    p.setFont("Helvetica", 10)

    total = 0
    cart_items_data = order_meta.get('cart_items_data', [])
    for item_data in cart_items_data:
        if y < 80:
            p.showPage()
            y = height - 50
        p.drawString(50, y, str(item_data['product_name'])[:40])
        p.drawRightString(370, y, f"₹{item_data['product_price']}")
        p.drawRightString(430, y, str(item_data['quantity']))
        p.drawRightString(545, y, f"₹{item_data['line_total']}")
        total += float(item_data['line_total'])
        y -= 18

    y -= 8
    p.line(380, y, 545, y)
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(500, y, "Total:")
    p.drawRightString(545, y, f"₹{order_meta.get('total_price', total):.2f}")

    p.showPage()
    p.save()
    return response