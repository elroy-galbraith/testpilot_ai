"""Initial migration for TestPilot AI models

Revision ID: 360162081875
Revises: 
Create Date: 2025-07-29 23:10:23.128912

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '360162081875'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create test_cases table
    op.create_table('test_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('spec', sa.Text(), nullable=False),
        sa.Column('generated_code', sa.Text(), nullable=True),
        sa.Column('framework', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_test_cases_id'), 'test_cases', ['id'], unique=False)
    op.create_index(op.f('ix_test_cases_title'), 'test_cases', ['title'], unique=False)
    
    # Create execution_results table
    op.create_table('execution_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('execution_time', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('screenshot_path', sa.String(length=500), nullable=True),
        sa.Column('video_path', sa.String(length=500), nullable=True),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.Column('browser_info', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_execution_results_id'), 'execution_results', ['id'], unique=False)
    
    # Create user_feedback table
    op.create_table('user_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_feedback_id'), 'user_feedback', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_user_feedback_id'), table_name='user_feedback')
    op.drop_table('user_feedback')
    
    op.drop_index(op.f('ix_execution_results_id'), table_name='execution_results')
    op.drop_table('execution_results')
    
    op.drop_index(op.f('ix_test_cases_title'), table_name='test_cases')
    op.drop_index(op.f('ix_test_cases_id'), table_name='test_cases')
    op.drop_table('test_cases') 