from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from . import db
from flask_login import login_required, current_user
from .model import Note, Expense, Category
import json
from datetime import datetime, timedelta
from sqlalchemy import extract, func, and_

views = Blueprint('views',__name__)

@views.route('/', methods = ['GET', 'POST'])
@login_required
def home():
    if request.method == "POST":
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description', '').strip()
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be greater than 0', category='error')
                return redirect(url_for('views.home'))
        except (ValueError, TypeError):
            flash('Please enter a valid amount', category='error')
            return redirect(url_for('views.home'))
            
        if not category:
            flash('Please select a category', category='error')
            return redirect(url_for('views.home'))
            
        new_expense = Expense(
            user_id=current_user.id,
            timestamp=datetime.utcnow(),
            category=category,
            amount=amount,
            description=description
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully', category='success')
        return redirect(url_for('views.home'))

    #  monthly summary
    current_month = datetime.now()
    monthly_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        extract('month', Expense.timestamp) == current_month.month,
        extract('year', Expense.timestamp) == current_month.year
    ).all()

    # Calculate totals 
    category_totals = {}
    total = 0
    for expense in monthly_expenses:
        total += expense.amount
        if expense.category in category_totals:
            category_totals[expense.category] += expense.amount
        else:
            category_totals[expense.category] = expense.amount

    # lấy 5 giao dịch gần đây nhất
    recent_expenses = Expense.query.filter(
        Expense.user_id == current_user.id
    ).order_by(Expense.timestamp.desc()).limit(5).all()

    # top spending categories
    top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

    return render_template(
        "home.html",
        user=current_user,
        total=total,
        category_totals=category_totals,
        current_month=current_month.strftime('%B %Y'),
        recent_expenses=recent_expenses,
        top_categories=top_categories
    )

@views.route('/delete-expense', methods=['POST'])
@login_required
def delete_expense():
    data = json.loads(request.data)
    expense_id = data['expenseId']
    expense = Expense.query.get(expense_id)
    if expense:
        if expense.user_id == current_user.id:
            db.session.delete(expense)
            db.session.commit()
    return jsonify({})

@views.route('/statistics')
@login_required
def statistics():
    # Get last 6 months of expenses
    six_months_ago = datetime.now() - timedelta(days=180)
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.timestamp >= six_months_ago
    ).all()

    # tính tổng số tiền và số giao dịch
    total_amount = sum(expense.amount for expense in expenses)
    total_transactions = len(expenses)

    # tính phần trăm
    category_percentages = {}
    for expense in expenses:
        if expense.category in category_percentages:
            category_percentages[expense.category] += expense.amount
        else:
            category_percentages[expense.category] = expense.amount

    # tính phần trăm
    for category in category_percentages:
        category_percentages[category] = (category_percentages[category] / total_amount * 100) if total_amount > 0 else 0

    # top 5 highest expenses
    top_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.timestamp >= six_months_ago
    ).order_by(Expense.amount.desc()).limit(5).all()

    return render_template(
        "statistics.html",
        user=current_user,
        total_amount=total_amount,
        total_transactions=total_transactions,
        category_percentages=category_percentages,
        top_expenses=top_expenses
    )

@views.route("/categories", methods=['GET', 'POST']) # thêm categories
@login_required
def categories():
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        color = request.form.get('color')
        
        if not name or not icon or not color:
            flash('Please fill in all fields', category='error')
            return redirect(url_for('views.categories'))
            
        new_category = Category(
            name=name,
            icon=icon,
            color=color,
            user_id=current_user.id
        )
        db.session.add(new_category)
        db.session.commit()
        
        flash('Category added successfully!', category='success')
        return redirect(url_for('views.categories'))
        
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template("categories.html", categories=categories)

@views.route("/get-category/<int:category_id>")
@login_required
def get_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'id': category.id,
        'name': category.name,
        'icon': category.icon,
        'color': category.color
    })

@views.route("/edit-category", methods=['POST'])
@login_required
def edit_category():
    category_id = request.form.get('category_id')
    name = request.form.get('name')
    icon = request.form.get('icon')
    color = request.form.get('color')
    
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    
    category.name = name
    category.icon = icon
    category.color = color
    
    db.session.commit()
    flash('Category updated successfully!', category='success')
    return redirect(url_for('views.categories'))

@views.route("/delete-category", methods=['POST'])
@login_required
def delete_category():
    data = request.get_json()
    category_id = data.get('categoryId')
    
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    
    
    default_category = Category.query.filter_by(name='Other', user_id=current_user.id).first()
    if default_category:
        Expense.query.filter_by(category_id=category_id).update({'category_id': default_category.id})
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'success': True})

  

  
