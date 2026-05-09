"""
Google Ads API 客户端工厂
每次调用时按 login_customer_id 创建独立客户端
"""
from google.ads.googleads.client import GoogleAdsClient
from app.core.config import settings


def get_google_ads_client(login_customer_id: str = None) -> GoogleAdsClient:
    """
    创建 Google Ads API 客户端。
    login_customer_id: MCC 经理账号 ID（不带横线），不传则用全局配置。
    """
    cid = (login_customer_id or settings.GOOGLE_ADS_LOGIN_CUSTOMER_ID).replace("-", "")

    config = {
        "developer_token": settings.GOOGLE_ADS_DEVELOPER_TOKEN,
        "client_id": settings.GOOGLE_ADS_CLIENT_ID,
        "client_secret": settings.GOOGLE_ADS_CLIENT_SECRET,
        "refresh_token": settings.GOOGLE_ADS_REFRESH_TOKEN,
        "use_proto_plus": settings.GOOGLE_ADS_USE_PROTO_PLUS,
    }
    if cid:
        config["login_customer_id"] = cid

    return GoogleAdsClient.load_from_dict(config)


def is_google_ads_configured() -> bool:
    """检查 Google Ads API 是否已配置好所有必要凭据"""
    return all([
        settings.GOOGLE_ADS_DEVELOPER_TOKEN,
        settings.GOOGLE_ADS_CLIENT_ID,
        settings.GOOGLE_ADS_CLIENT_SECRET,
        settings.GOOGLE_ADS_REFRESH_TOKEN,
    ])
