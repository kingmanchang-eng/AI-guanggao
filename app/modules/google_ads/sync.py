"""
Google Ads 数据同步模块
拉取 Campaign / Keyword / SearchTerm 快照写入 Supabase
"""
import logging
from datetime import date, timedelta
from app.db.supabase_client import get_client
from app.modules.google_ads.client import get_google_ads_client, is_google_ads_configured

logger = logging.getLogger(__name__)

# 默认拉取最近 30 天数据
DEFAULT_DAYS = 30


def sync_website_data(website_id: str, customer_id: str,
                      login_customer_id: str, manager_account_id: str):
    """同步一个网站对应广告账号的全量快照数据"""
    if not is_google_ads_configured():
        logger.warning("Google Ads API 未配置，跳过同步")
        return

    client = get_google_ads_client(login_customer_id)
    cid = customer_id.replace("-", "")

    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=DEFAULT_DAYS - 1)
    date_range = f"segments.date BETWEEN '{start_date}' AND '{end_date}'"

    _sync_campaigns(client, cid, website_id, manager_account_id, customer_id, date_range)
    _sync_ad_groups(client, cid, website_id, manager_account_id, customer_id, date_range)
    _sync_keywords(client, cid, website_id, manager_account_id, customer_id, date_range)
    _sync_search_terms(client, cid, website_id, manager_account_id, customer_id, date_range)

    logger.info(f"同步完成: website={website_id} customer={customer_id}")


def _sync_campaigns(client, cid, website_id, manager_account_id, customer_id, date_range):
    db = get_client()
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            segments.date,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_per_conversion
        FROM campaign
        WHERE {date_range}
          AND campaign.status != 'REMOVED'
        ORDER BY segments.date DESC
        LIMIT 500
    """

    rows = []
    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            rows.append({
                "website_id": website_id,
                "manager_account_id": manager_account_id,
                "customer_id": customer_id,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "date": row.segments.date,
                "metrics_json": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost_micros": row.metrics.cost_micros,
                    "cost_usd": round(row.metrics.cost_micros / 1_000_000, 4),
                    "conversions": row.metrics.conversions,
                    "ctr": round(row.metrics.ctr, 6),
                    "average_cpc_micros": row.metrics.average_cpc,
                    "cost_per_conversion": round(row.metrics.cost_per_conversion, 4),
                    "campaign_status": row.campaign.status.name,
                },
            })
    except Exception as e:
        logger.error(f"Campaign 同步失败 customer={cid}: {e}")
        return

    if rows:
        db.table("campaign_snapshots").upsert(rows, on_conflict="website_id,customer_id,campaign_id,date").execute()
        logger.info(f"Campaign 快照写入 {len(rows)} 条")


def _sync_ad_groups(client, cid, website_id, manager_account_id, customer_id, date_range):
    db = get_client()
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id,
            ad_group.id,
            ad_group.name,
            ad_group.status,
            ad_group.type,
            segments.date,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc
        FROM ad_group
        WHERE {date_range}
          AND ad_group.status != 'REMOVED'
        ORDER BY segments.date DESC
        LIMIT 1000
    """

    rows = []
    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            rows.append({
                "website_id": website_id,
                "manager_account_id": manager_account_id,
                "customer_id": customer_id,
                "campaign_id": str(row.campaign.id),
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "date": row.segments.date,
                "metrics_json": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost_micros": row.metrics.cost_micros,
                    "cost_usd": round(row.metrics.cost_micros / 1_000_000, 4),
                    "conversions": row.metrics.conversions,
                    "ctr": round(row.metrics.ctr, 6),
                    "average_cpc_micros": row.metrics.average_cpc,
                    "ad_group_status": row.ad_group.status.name,
                    "ad_group_type": row.ad_group.type_.name,
                },
            })
    except Exception as e:
        logger.error(f"AdGroup 同步失败 customer={cid}: {e}")
        return

    if rows:
        db.table("ad_group_snapshots").upsert(
            rows,
            on_conflict="website_id,customer_id,campaign_id,ad_group_id,date"
        ).execute()
        logger.info(f"AdGroup 快照写入 {len(rows)} 条")


def _sync_keywords(client, cid, website_id, manager_account_id, customer_id, date_range):
    db = get_client()
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id,
            ad_group.id,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            segments.date,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc
        FROM keyword_view
        WHERE {date_range}
          AND ad_group_criterion.status != 'REMOVED'
        ORDER BY segments.date DESC
        LIMIT 1000
    """

    rows = []
    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            rows.append({
                "website_id": website_id,
                "manager_account_id": manager_account_id,
                "customer_id": customer_id,
                "campaign_id": str(row.campaign.id),
                "ad_group_id": str(row.ad_group.id),
                "keyword_text": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "date": row.segments.date,
                "metrics_json": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost_micros": row.metrics.cost_micros,
                    "cost_usd": round(row.metrics.cost_micros / 1_000_000, 4),
                    "conversions": row.metrics.conversions,
                    "ctr": round(row.metrics.ctr, 6),
                    "average_cpc_micros": row.metrics.average_cpc,
                    "keyword_status": row.ad_group_criterion.status.name,
                },
            })
    except Exception as e:
        logger.error(f"Keyword 同步失败 customer={cid}: {e}")
        return

    if rows:
        db.table("keyword_snapshots").upsert(
            rows,
            on_conflict="website_id,customer_id,campaign_id,ad_group_id,keyword_text,match_type,date"
        ).execute()
        logger.info(f"Keyword 快照写入 {len(rows)} 条")


def _sync_search_terms(client, cid, website_id, manager_account_id, customer_id, date_range):
    db = get_client()
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id,
            ad_group.id,
            search_term_view.search_term,
            segments.date,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr
        FROM search_term_view
        WHERE {date_range}
          AND metrics.impressions > 0
        ORDER BY metrics.clicks DESC
        LIMIT 500
    """

    rows = []
    try:
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            rows.append({
                "website_id": website_id,
                "manager_account_id": manager_account_id,
                "customer_id": customer_id,
                "campaign_id": str(row.campaign.id),
                "ad_group_id": str(row.ad_group.id),
                "search_term": row.search_term_view.search_term,
                "date": row.segments.date,
                "metrics_json": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost_micros": row.metrics.cost_micros,
                    "cost_usd": round(row.metrics.cost_micros / 1_000_000, 4),
                    "conversions": row.metrics.conversions,
                    "ctr": round(row.metrics.ctr, 6),
                },
            })
    except Exception as e:
        logger.error(f"SearchTerm 同步失败 customer={cid}: {e}")
        return

    if rows:
        db.table("search_term_snapshots").upsert(
            rows,
            on_conflict="website_id,customer_id,campaign_id,ad_group_id,search_term,date"
        ).execute()
        logger.info(f"SearchTerm 快照写入 {len(rows)} 条")
