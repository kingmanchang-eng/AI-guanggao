"""
Google Ads API mutate 执行器
把 AI 生成的 action 转换成真实的 Google Ads API 调用
"""
import logging
from google.ads.googleads.errors import GoogleAdsException
from app.modules.google_ads.client import get_google_ads_client

logger = logging.getLogger(__name__)


def execute_action(action: dict, binding: dict) -> tuple[bool, dict | None, str | None]:
    """
    执行单条 AI 动作。
    返回 (success, response_dict, error_message)
    """
    customer_id = binding["customer_id"].replace("-", "")
    login_customer_id = binding.get("login_customer_id") or binding.get("manager_account_id")
    action_type = action.get("action_type", "")
    payload = action.get("payload_json", action)

    try:
        client = get_google_ads_client(login_customer_id)
    except Exception as e:
        return False, None, f"客户端初始化失败: {e}"

    handlers = {
        "UPDATE_CAMPAIGN_BUDGET": _update_campaign_budget,
        "UPDATE_CAMPAIGN_STATUS": _update_campaign_status,
        "UPDATE_AD_GROUP_STATUS": _update_ad_group_status,
        "ADD_KEYWORD": _add_keyword,
        "PAUSE_KEYWORD": _pause_keyword,
        "ADD_NEGATIVE_KEYWORD": _add_negative_keyword,
        "PAUSE_AD": _pause_ad,
        "CREATE_RESPONSIVE_SEARCH_AD": _create_responsive_search_ad,
    }

    handler = handlers.get(action_type)
    if not handler:
        return False, None, f"不支持的 action_type: {action_type}"

    try:
        result = handler(client, customer_id, payload)
        return True, result, None
    except GoogleAdsException as ex:
        errors = "; ".join([e.message for e in ex.failure.errors])
        logger.error(f"GoogleAdsException [{action_type}]: {errors}")
        return False, None, errors
    except Exception as e:
        logger.error(f"执行失败 [{action_type}]: {e}")
        return False, None, str(e)


# ──────────────────────────────────────────────
# 具体操作实现
# ──────────────────────────────────────────────

def _update_campaign_budget(client, customer_id: str, payload: dict) -> dict:
    """调整广告系列预算"""
    campaign_budget_service = client.get_service("CampaignBudgetService")
    campaign_service = client.get_service("CampaignService")
    googleads_service = client.get_service("GoogleAdsService")

    campaign_id = payload["campaign_id"]

    # 先查当前 budget resource name
    query = f"""
        SELECT campaign.campaign_budget
        FROM campaign
        WHERE campaign.id = {campaign_id}
        LIMIT 1
    """
    response = googleads_service.search(customer_id=customer_id, query=query)
    row = next(iter(response))
    budget_resource = row.campaign.campaign_budget

    # 更新预算金额
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.update
    budget.resource_name = budget_resource
    new_budget_usd = float(payload["new_budget_usd"])
    budget.amount_micros = int(new_budget_usd * 1_000_000)

    field_mask = client.get_type("FieldMask")
    field_mask.paths.append("amount_micros")
    budget_op.update_mask.CopyFrom(field_mask)

    result = campaign_budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[budget_op]
    )
    return {"updated_budget_resource": result.results[0].resource_name,
            "new_budget_usd": new_budget_usd}


def _update_campaign_status(client, customer_id: str, payload: dict) -> dict:
    """暂停或启用广告系列"""
    campaign_service = client.get_service("CampaignService")
    campaign_id = payload["campaign_id"]
    new_status = payload.get("status", "PAUSED")  # ENABLED / PAUSED

    campaign_op = client.get_type("CampaignOperation")
    campaign = campaign_op.update
    campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
    campaign.status = client.enums.CampaignStatusEnum[new_status]

    field_mask = client.get_type("FieldMask")
    field_mask.paths.append("status")
    campaign_op.update_mask.CopyFrom(field_mask)

    result = campaign_service.mutate_campaigns(
        customer_id=customer_id, operations=[campaign_op]
    )
    return {"resource_name": result.results[0].resource_name, "status": new_status}


def _update_ad_group_status(client, customer_id: str, payload: dict) -> dict:
    """暂停或启用广告组"""
    ad_group_service = client.get_service("AdGroupService")
    ad_group_id = payload["ad_group_id"]
    new_status = payload.get("status", "PAUSED")

    op = client.get_type("AdGroupOperation")
    ag = op.update
    ag.resource_name = ad_group_service.ad_group_path(customer_id, ad_group_id)
    ag.status = client.enums.AdGroupStatusEnum[new_status]

    field_mask = client.get_type("FieldMask")
    field_mask.paths.append("status")
    op.update_mask.CopyFrom(field_mask)

    result = ad_group_service.mutate_ad_groups(customer_id=customer_id, operations=[op])
    return {"resource_name": result.results[0].resource_name, "status": new_status}


def _add_keyword(client, customer_id: str, payload: dict) -> dict:
    """添加关键词"""
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")
    ad_group_service = client.get_service("AdGroupService")

    op = client.get_type("AdGroupCriterionOperation")
    criterion = op.create
    criterion.ad_group = ad_group_service.ad_group_path(customer_id, payload["ad_group_id"])
    criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
    criterion.keyword.text = payload["keyword_text"]
    match_type = payload.get("match_type", "BROAD")
    criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type]

    result = ad_group_criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[op]
    )
    return {"resource_name": result.results[0].resource_name,
            "keyword": payload["keyword_text"], "match_type": match_type}


def _pause_keyword(client, customer_id: str, payload: dict) -> dict:
    """暂停关键词"""
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")

    op = client.get_type("AdGroupCriterionOperation")
    criterion = op.update
    criterion.resource_name = payload["criterion_resource_name"]
    criterion.status = client.enums.AdGroupCriterionStatusEnum.PAUSED

    field_mask = client.get_type("FieldMask")
    field_mask.paths.append("status")
    op.update_mask.CopyFrom(field_mask)

    result = ad_group_criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[op]
    )
    return {"resource_name": result.results[0].resource_name, "status": "PAUSED"}


def _add_negative_keyword(client, customer_id: str, payload: dict) -> dict:
    """添加否定关键词（广告组级别）"""
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")
    ad_group_service = client.get_service("AdGroupService")

    op = client.get_type("AdGroupCriterionOperation")
    criterion = op.create
    criterion.ad_group = ad_group_service.ad_group_path(customer_id, payload["ad_group_id"])
    criterion.negative = True
    criterion.keyword.text = payload["keyword_text"]
    match_type = payload.get("match_type", "BROAD")
    criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type]

    result = ad_group_criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[op]
    )
    return {"resource_name": result.results[0].resource_name,
            "negative_keyword": payload["keyword_text"], "match_type": match_type}


def _pause_ad(client, customer_id: str, payload: dict) -> dict:
    """暂停广告"""
    ad_group_ad_service = client.get_service("AdGroupAdService")

    op = client.get_type("AdGroupAdOperation")
    ad = op.update
    ad.resource_name = payload["ad_resource_name"]
    ad.status = client.enums.AdGroupAdStatusEnum.PAUSED

    field_mask = client.get_type("FieldMask")
    field_mask.paths.append("status")
    op.update_mask.CopyFrom(field_mask)

    result = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=customer_id, operations=[op]
    )
    return {"resource_name": result.results[0].resource_name, "status": "PAUSED"}


def _create_responsive_search_ad(client, customer_id: str, payload: dict) -> dict:
    """创建响应式搜索广告"""
    ad_group_ad_service = client.get_service("AdGroupAdService")
    ad_group_service = client.get_service("AdGroupService")

    op = client.get_type("AdGroupAdOperation")
    ad_group_ad = op.create
    ad_group_ad.ad_group = ad_group_service.ad_group_path(customer_id, payload["ad_group_id"])
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

    rsa = ad_group_ad.ad.responsive_search_ad
    ad_group_ad.ad.final_urls.append(payload["final_url"])

    # 添加标题（最多15个，至少3个）
    for i, headline in enumerate(payload.get("headlines", [])[:15]):
        asset = client.get_type("AdTextAsset")
        asset.text = headline[:30]  # 标题最多30字符
        rsa.headlines.append(asset)

    # 添加描述（最多4个，至少2个）
    for desc in payload.get("descriptions", [])[:4]:
        asset = client.get_type("AdTextAsset")
        asset.text = desc[:90]  # 描述最多90字符
        rsa.descriptions.append(asset)

    result = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=customer_id, operations=[op]
    )
    return {
        "resource_name": result.results[0].resource_name,
        "final_url": payload["final_url"],
        "headlines_count": len(payload.get("headlines", [])),
        "descriptions_count": len(payload.get("descriptions", [])),
    }
