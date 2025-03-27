from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from . import db
from flask_login import  login_required, current_user
from .model import Note, Expense
import json
from datetime import datetime
from sqlalchemy import extract, func

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

    # monthly summary
    current_month = datetime.now()
    monthly_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        extract('month', Expense.timestamp) == current_month.month,
        extract('year', Expense.timestamp) == current_month.year
    ).all()

    # Calculate 
    category_totals = {}
    total = 0
    for expense in monthly_expenses:
        total += expense.amount
        if expense.category in category_totals:
            category_totals[expense.category] += expense.amount
        else:
            category_totals[expense.category] = expense.amount

    return render_template(
        "home.html",
        user=current_user,
        total=total,
        category_totals=category_totals,
        current_month=current_month.strftime('%B %Y')
    )
    

@views.route('/delete-expense', methods=['POST'])
def delete_expense():
    """  data = json.loads(request.data)
    expense_Id = data['noteId']
    #truy cập note có id, nếu tồn tại thì xóa note đi
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    #trả về emty response
    return jsonify({})"""
    data = json.loads(request.data)
    expense_id = data['expenseId']
    expense = Expense.query.get(expense_id)
    if expense:
        if expense.user_id == current_user.id:
            db.session.delete(expense)
            db.session.commit()
    return jsonify({})


    
  

  
