"""
Google Ads 广告系列构建器
按顺序创建：预算 → 广告系列 → 广告组 → 关键词 → 否定关键词 → 响应式搜索广告
任一步骤失败不影响其他广告组的创建，错误收集后统一返回
"""
import logging
from app.modules.google_ads.client import get_google_ads_client

logger = logging.getLogger(__name__)


def build_campaign_from_plan(
    plan: dict,
    customer_id: str,
    login_customer_id: str,
    final_url: str,
    start_paused: bool = True,
) -> dict:
    """
    执行完整广告系列创建流程。
    返回 result dict，包含所有已创建资源和错误列表。
    """
    cid = customer_id.replace("-", "")
    client = get_google_ads_client(login_customer_id)

    result = {
        "budget_resource": None,
        "campaign_resource": None,
        "campaign_name": plan.get("campaign_name", ""),
        "ad_groups": [],
        "keywords_created": 0,
        "negative_keywords_created": 0,
        "ads_created": 0,
        "errors": [],
    }

    # Step 1: 创建预算
    try:
        result["budget_resource"] = _create_budget(client, cid, plan)
        logger.info(f"预算创建成功: {result['budget_resource']}")
    except Exception as e:
        result["errors"].append(f"创建预算失败: {e}")
        return result

    # Step 2: 创建广告系列
    try:
        result["campaign_resource"] = _create_campaign(
            client, cid, plan, result["budget_resource"], start_paused
        )
        logger.info(f"广告系列创建成功: {result['campaign_resource']}")
    except Exception as e:
        result["errors"].append(f"创建广告系列失败: {e}")
        return result

    # Step 3: 逐个创建广告组
    for ag_plan in plan.get("ad_groups", []):
        ag_summary = {"name": ag_plan.get("name", ""), "resource": None, "errors": []}
        try:
            ag_resource = _create_ad_group(client, cid, ag_plan, result["campaign_resource"])
            ag_summary["resource"] = ag_resource

            kw_n = _add_keywords(client, cid, ag_plan.get("keywords", []), ag_resource)
            result["keywords_created"] += kw_n

            neg_n = _add_negative_keywords(client, cid, ag_plan.get("negative_keywords", []), ag_resource)
            result["negative_keywords_created"] += neg_n

            headlines = ag_plan.get("headlines", [])
            descriptions = ag_plan.get("descriptions", [])
            if len(headlines) >= 3 and len(descriptions) >= 2:
                _create_rsa(client, cid, headlines, descriptions, ag_resource, final_url)
                result["ads_created"] += 1

            logger.info(f"广告组 '{ag_plan.get('name')}' 创建完成，关键词 {kw_n} 个")
        except Exception as e:
            ag_summary["errors"].append(str(e))
            result["errors"].append(f"广告组 '{ag_plan.get('name')}' 失败: {e}")
            logger.error(f"广告组创建失败: {e}")

        result["ad_groups"].append(ag_summary)

    return result


def _create_budget(client, cid: str, plan: dict) -> str:
    svc = client.get_service("CampaignBudgetService")
    op = client.get_type("CampaignBudgetOperation")
    b = op.create
    b.name = f"Budget – {plan['campaign_name'][:100]}"
    b.amount_micros = int(float(plan.get("daily_budget_usd", 50)) * 1_000_000)
    b.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    b.explicitly_shared = False
    r = svc.mutate_campaign_budgets(customer_id=cid, operations=[op])
    return r.results[0].resource_name


def _create_campaign(client, cid: str, plan: dict, budget_resource: str, start_paused: bool) -> str:
    svc = client.get_service("CampaignService")
    op = client.get_type("CampaignOperation")
    c = op.create
    c.name = plan["campaign_name"]
    c.status = (
        client.enums.CampaignStatusEnum.PAUSED
        if start_paused
        else client.enums.CampaignStatusEnum.ENABLED
    )
    c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    c.campaign_budget = budget_resource

    bidding = plan.get("bidding_strategy", "MANUAL_CPC")
    if bidding == "MANUAL_CPC":
        c.manual_cpc.enhanced_cpc_enabled = False
    elif bidding == "TARGET_CPA" and plan.get("target_cpa_usd"):
        c.target_cpa.target_cpa_micros = int(float(plan["target_cpa_usd"]) * 1_000_000)
    # MAXIMIZE_CONVERSIONS: leave bidding fields empty, API infers

    c.network_settings.target_google_search = True
    c.network_settings.target_search_network = True
    c.network_settings.target_content_network = False

    r = svc.mutate_campaigns(customer_id=cid, operations=[op])
    return r.results[0].resource_name


def _create_ad_group(client, cid: str, ag_plan: dict, campaign_resource: str) -> str:
    svc = client.get_service("AdGroupService")
    op = client.get_type("AdGroupOperation")
    ag = op.create
    ag.name = ag_plan["name"]
    ag.campaign = campaign_resource
    ag.status = client.enums.AdGroupStatusEnum.ENABLED
    ag.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
    if ag_plan.get("cpc_bid_usd"):
        ag.cpc_bid_micros = int(float(ag_plan["cpc_bid_usd"]) * 1_000_000)
    r = svc.mutate_ad_groups(customer_id=cid, operations=[op])
    return r.results[0].resource_name


def _add_keywords(client, cid: str, keywords: list, ag_resource: str) -> int:
    if not keywords:
        return 0
    svc = client.get_service("AdGroupCriterionService")
    ops = []
    for kw in keywords[:20]:
        op = client.get_type("AdGroupCriterionOperation")
        cr = op.create
        cr.ad_group = ag_resource
        cr.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        cr.keyword.text = kw["text"][:80]
        cr.keyword.match_type = client.enums.KeywordMatchTypeEnum[kw.get("match_type", "PHRASE")]
        ops.append(op)
    if ops:
        svc.mutate_ad_group_criteria(customer_id=cid, operations=ops)
    return len(ops)


def _add_negative_keywords(client, cid: str, neg_keywords: list, ag_resource: str) -> int:
    if not neg_keywords:
        return 0
    svc = client.get_service("AdGroupCriterionService")
    ops = []
    for kw in neg_keywords[:10]:
        op = client.get_type("AdGroupCriterionOperation")
        cr = op.create
        cr.ad_group = ag_resource
        cr.negative = True
        cr.keyword.text = kw["text"][:80]
        cr.keyword.match_type = client.enums.KeywordMatchTypeEnum[kw.get("match_type", "BROAD")]
        ops.append(op)
    if ops:
        svc.mutate_ad_group_criteria(customer_id=cid, operations=ops)
    return len(ops)


def _create_rsa(
    client, cid: str, headlines: list, descriptions: list, ag_resource: str, final_url: str
):
    svc = client.get_service("AdGroupAdService")
    op = client.get_type("AdGroupAdOperation")
    aa = op.create
    aa.ad_group = ag_resource
    aa.status = client.enums.AdGroupAdStatusEnum.ENABLED
    aa.ad.final_urls.append(final_url)

    rsa = aa.ad.responsive_search_ad
    for h in headlines[:15]:
        asset = client.get_type("AdTextAsset")
        asset.text = h[:30]
        rsa.headlines.append(asset)
    for d in descriptions[:4]:
        asset = client.get_type("AdTextAsset")
        asset.text = d[:90]
        rsa.descriptions.append(asset)

    svc.mutate_ad_group_ads(customer_id=cid, operations=[op])
