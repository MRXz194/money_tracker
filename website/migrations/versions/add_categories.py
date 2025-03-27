"""add categories

Revision ID: add_categories
Revises: previous_revision
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_categories'
down_revision = None  # Update this with your previous migration revision
branch_labels = None
depends_on = None

def upgrade():
    # Create categories table
    op.create_table('category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add category_id to expense table
    op.add_column('expense', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'expense', 'category', ['category_id'], ['id'])

    # Migrate existing expenses to use categories
    # First, create default categories for each user
    op.execute("""
        INSERT INTO category (name, icon, color, user_id, created_at)
        SELECT DISTINCT 'Other', 'fas fa-tag', '#6c757d', user_id, CURRENT_TIMESTAMP
        FROM expense
        WHERE user_id NOT IN (SELECT user_id FROM category)
    """)

    # Then, update expenses to use the appropriate category
    op.execute("""
        UPDATE expense e
        SET category_id = (
            SELECT c.id
            FROM category c
            WHERE c.user_id = e.user_id
            AND c.name = e.category
            LIMIT 1
        )
    """)

    # Drop the old category column
    op.drop_column('expense', 'category')

def downgrade():
    # Add back the category column
    op.add_column('expense', sa.Column('category', sa.String(length=100), nullable=True))

    # Migrate data back
    op.execute("""
        UPDATE expense e
        SET category = (
            SELECT c.name
            FROM category c
            WHERE c.id = e.category_id
            LIMIT 1
        )
    """)

    # Drop the foreign key and category_id column
    op.drop_constraint(None, 'expense', type_='foreignkey')
    op.drop_column('expense', 'category_id')

    # Drop the category table
    op.drop_table('category') 