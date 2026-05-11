-- Migration: 001_create_ad_group_snapshots
-- Created: 2026-05-09
-- 创建 AdGroup 每日快照表，与 campaign_snapshots / keyword_snapshots 保持一致风格

CREATE TABLE IF NOT EXISTS ad_group_snapshots (
    id              bigserial PRIMARY KEY,
    website_id      uuid        NOT NULL,
    manager_account_id uuid     NOT NULL,
    customer_id     text        NOT NULL,
    campaign_id     text        NOT NULL,
    ad_group_id     text        NOT NULL,
    ad_group_name   text        NOT NULL DEFAULT '',
    date            date        NOT NULL,
    metrics_json    jsonb       NOT NULL DEFAULT '{}',
    created_at      timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ad_group_snapshots_unique
        UNIQUE (website_id, customer_id, campaign_id, ad_group_id, date)
);

-- 加速按网站+日期范围查询（AI 分析最常用）
CREATE INDEX IF NOT EXISTS idx_ad_group_snapshots_website_date
    ON ad_group_snapshots (website_id, date DESC);

-- 加速按 campaign_id 聚合
CREATE INDEX IF NOT EXISTS idx_ad_group_snapshots_campaign
    ON ad_group_snapshots (website_id, customer_id, campaign_id, date DESC);

-- 开启 RLS（与其他 snapshot 表保持一致，service_role 可绕过）
ALTER TABLE ad_group_snapshots ENABLE ROW LEVEL SECURITY;
