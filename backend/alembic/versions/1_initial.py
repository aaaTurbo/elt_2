
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("keitaro_campaign_id", sa.BigInteger(), unique=True, nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("geo_code", sa.String(2), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("current_version_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "streams",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True),
                  sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keitaro_stream_id", sa.BigInteger(), unique=True, nullable=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("redirect_url", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "stream_offers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("stream_id", UUID(as_uuid=True),
                  sa.ForeignKey("streams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keitaro_offer_id", sa.BigInteger(), nullable=False),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("is_weight_fixed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted_in_kt", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_in_kt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "campaign_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True),
                  sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("campaign_id", "version_number"),
    )

    op.create_table(
        "edit_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True),
                  sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "keitaro_push_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True),
                  sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("edit_session_id", UUID(as_uuid=True),
                  sa.ForeignKey("edit_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("idempotency_key", sa.String(64), unique=True, nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("response", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for t in (
        "keitaro_push_logs", "edit_sessions", "campaign_versions",
        "stream_offers", "streams", "campaigns",
    ):
        op.drop_table(t)
